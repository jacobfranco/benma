"""Offline mapping regressions; real excerpts are labeled separately from synthetic structures."""

import copy
import hashlib
import json
import socket
from pathlib import Path

import pytest
from pydantic import ValidationError

from benchmark.pronunciation_v2 import connected_replay as replay
from benchmark.pronunciation_v2 import connected_speech_probe as probe
from benchmark.pronunciation_v2.connected_mapping import grapheme_candidates
from benchmark.pronunciation_v2.connected_schema import Audio, Record
from benchmark.pronunciation_v2.test_connected_speech import azure, make, phone, word

HERE = Path(__file__).parent
EXCERPTS = json.loads((HERE / "fixtures/connected-real-mapping-excerpts.json").read_text())


def grapheme(character, start, duration):
    return {"Grapheme": character, "Offset": start * 10000, "Duration": duration * 10000}


def explicit(text="水行", entries=None):
    value = word(text)
    value["Syllables"] = (
        entries
        if entries is not None
        else [grapheme(text[0], 100, 200), grapheme(text[1], 400, 300)]
    )
    return azure([value])


def test_ambiguous_reading_keeps_exact_timing_and_markdown():
    raw = explicit()
    r = make("水行", azure_raw=raw)
    unit = r.units[1]
    assert unit.reading.ambiguous
    assert unit.reading.pinyin is None
    assert unit.timing.start_ms == 400
    assert unit.timing.end_ms == 700
    assert unit.provider_timing.raw_entry == raw["NBest"][0]["Words"][0]["Syllables"][1]
    assert unit.provider_timing.raw_source == "/NBest/0/Words/0/Syllables/1"
    section = probe.markdown(r).split("## Unit u1: 行")[1]
    assert "Timing: 400-700 ms; source azure_provider_grapheme" in section
    assert "Reading: unresolved" in section
    assert not unit.phones
    assert "syllable_timing_unresolved" not in unit.quality_flags


def test_missing_span_stays_missing_even_with_phone_span():
    raw = explicit("水果")
    w = raw["NBest"][0]["Words"][0]
    del w["Syllables"][1]["Offset"]
    w["Phonemes"] = [phone("shui 3", 100, 200), phone("guo 3", 400, 300)]
    record = make("水果", azure_raw=raw)
    assert record.units[0].timing is not None
    assert record.units[1].timing is None
    assert "word[0]:grapheme[1]:missing_or_invalid_timing" in record.alignment.issues


@pytest.mark.parametrize("tier", [None, []])
def test_phone_counts_never_invent_multicharacter_boundaries(tier):
    raw = azure([word("贵州", phones=[phone("gui4", 100, 200), phone("zhou1", 400, 300)])])
    if tier is not None:
        raw["NBest"][0]["Words"][0]["Syllables"] = tier
    record = make("贵州", azure_raw=raw)
    assert record.alignment.words[0].timing is not None
    assert all(u.timing is None for u in record.units)


@pytest.mark.parametrize(
    "tier",
    [
        [grapheme("水", 100, 200)],
        [grapheme("水", 100, 200), grapheme("过", 400, 300)],
        [grapheme("果", 100, 200), grapheme("水", 400, 300)],
        [grapheme("水果", 100, 600)],
        [grapheme("水", 100, 200), grapheme("果", 400, 200), grapheme("了", 600, 100)],
        {"Grapheme": "水果"},
    ],
)
def test_exact_grapheme_sequence_required(tier):
    record = make("水果", azure_raw=explicit("水果", tier))
    assert all(u.timing is None for u in record.units)
    assert "word[0]:grapheme_sequence_conflict" in record.alignment.issues


@pytest.mark.parametrize(
    "tier",
    [
        [grapheme("水", 400, 200), grapheme("果", 100, 200)],
        [grapheme("水", 100, 400), grapheme("果", 400, 300)],
        [grapheme("水", 98, 200), grapheme("果", 400, 300)],
        [grapheme("水", 100, 200), grapheme("果", 400, 302)],
    ],
)
def test_invalid_order_overlap_and_word_containment_abstain(tier):
    record = make("水果", azure_raw=explicit("水果", tier))
    assert all(u.timing is None for u in record.units)
    assert "word[0]:invalid_or_nonmonotonic_grapheme_span" in record.alignment.issues


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("Offset", -1),
        ("Offset", True),
        ("Duration", 0),
        ("Duration", -1),
    ],
)
def test_invalid_individual_span_never_accepted(field, value):
    raw = explicit("水果")
    raw["NBest"][0]["Words"][0]["Syllables"][1][field] = value
    record = make("水果", azure_raw=raw)
    assert record.units[1].timing is None


def test_numeric_nonfinite_spans_rejected_before_schema():
    for value in (float("inf"), float("nan")):
        raw = explicit("水果")
        raw["NBest"][0]["Words"][0]["Syllables"][1]["Offset"] = value
        _, candidates, issues = grapheme_candidates(raw, "水果")
        assert len(candidates) == 1
        assert issues


@pytest.mark.parametrize("error", ["Omission", "Insertion"])
def test_provider_miscue_never_assigned(error):
    raw = explicit("水果")
    raw["NBest"][0]["Words"][0]["ErrorType"] = error
    record = make("水果", azure_raw=raw)
    assert all(u.timing is None for u in record.units)


def test_same_pinyin_different_character_cannot_map():
    record = make("那里", azure_raw=explicit("哪里"))
    assert all(u.timing is None for u in record.units)
    assert record.alignment.issues == ["asr_timing_text_conflict"]


def test_repeated_word_cannot_search_forward_or_skip():
    raw = explicit("水果")
    record = make("水果水果", azure_raw=raw)
    assert all(u.timing is None for u in record.units)


def test_phone_attachment_needs_base_and_exact_span_but_timing_does_not():
    raw = explicit("贵州")
    raw["NBest"][0]["Words"][0]["Phonemes"] = [
        phone("guang 3", 100, 200),
        phone("zhou 1", 401, 299),
    ]
    record = make("贵州", azure_raw=raw)
    assert all(u.timing for u in record.units)
    assert not any(u.phones for u in record.units)
    assert record.alignment.raw_response == raw


@pytest.mark.parametrize("capture", EXCERPTS["captures"], ids=lambda c: c["study_id"])
def test_derived_real_mapping_excerpt(capture):
    raw = capture["azure_raw"]
    kwargs = dict(
        recording_id=capture["recording_id"],
        audio=Audio(**capture["audio"]),
        provider="saved_real_excerpt",
        evidence={"transcript": capture["perceived_text"]},
        raw_response=None,
        azure_raw=raw,
    )
    free = probe.build_record(**kwargs)
    targeted = probe.build_record(**kwargs, target=capture["intended_text"])
    assert all(u.timing for u in targeted.units)
    assert all(u.timing_source == "azure_provider_grapheme" for u in targeted.units)
    assert not targeted.alignment.issues
    assert free.perception == targeted.perception
    assert free.alignment == targeted.alignment
    for a, b in zip(free.units, targeted.units, strict=True):
        for field in ("reading", "timing", "provider_timing", "phones", "pitch"):
            assert getattr(a, field) == getattr(b, field)
        evidence = b.provider_timing
        g = raw["NBest"][0]["Words"][evidence.word_index]["Syllables"][evidence.grapheme_index]
        assert b.timing.start_ms == pytest.approx(g["Offset"] / 10000)
        assert b.timing.duration_ms == pytest.approx(g["Duration"] / 10000)
    if capture["study_id"] == "S13":
        assert targeted.perception.raw_transcript == "我要去贵州。"
        assert targeted.alignment.reference_text == "我要去贵州。"
        gui = next(u for u in targeted.units if u.perceived_text == "贵")
        assert gui.reading.pinyin == "guì"
        assert gui.reading.context_text == "贵州"
        assert gui.target_comparison.operation == "substitution"
        assert gui.target_comparison.intended == "广"
        assert gui.target_comparison.expectation.reading.pinyin == "guǎng"
        assert gui.target_comparison.diagnosis == "not_inferred_from_text"
        assert gui.phones[0].label == "gui 4"
    for u in targeted.units:
        for p in u.phones:
            assert p.semantics == "reference_label_not_observed_phone"
            assert p.score == p.raw_entry["AccuracyScore"]
        assert u.judgment == "INSUFFICIENT EVIDENCE"


def test_existing_phrase_context_resolves_polyphone_without_target():
    raw = explicit("银行")
    a = make("银行", azure_raw=raw, target="行走")
    b = make("银行", azure_raw=raw)
    assert a.units[1].reading == b.units[1].reading
    assert a.units[1].reading.pinyin == "háng"
    assert a.units[1].reading.status == "phrase"


@pytest.mark.parametrize(
    ("phrase", "unresolved"),
    [
        ("天气", ["气"]),
        ("晚上", ["上"]),
        ("吃饭", ["吃"]),
        ("水果", ["果"]),
        ("我要", ["要"]),
        ("哪种", ["哪", "种"]),
        ("说说", ["说", "说"]),
    ],
)
def test_dictionary_gaps_remain_ambiguous_but_timed(phrase, unresolved):
    record = make(phrase, azure_raw=explicit(phrase))
    assert [u.perceived_text for u in record.units if u.reading.ambiguous] == unresolved
    assert all(u.timing for u in record.units)
    # Regression against quietly selecting the first heteronym, or using a provider phone.
    assert all(u.reading.pinyin is None for u in record.units if u.reading.ambiguous)


def test_replay_no_io_ports_and_provenance_preserved(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("offline replay invoked network, audio or acoustic extraction")

    for name in (
        "run_live",
        "request_azure_speech",
        "build_perception_provider",
        "inspect_audio",
        "canonicalize",
    ):
        monkeypatch.setattr(probe, name, forbidden)
    monkeypatch.setattr(probe.PraatAcousticAnalyzer, "analyze", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    original = make(
        "水行",
        azure_raw=explicit(),
        acoustics={
            "f0": [
                {
                    "timestamp_seconds": 0.5,
                    "f0_hz": 150,
                    "selected_f0_hz": 150,
                    "quality_usable": True,
                }
            ]
        },
    )
    original = original.model_copy(
        update={
            "audio": Audio(
                path="/does/not/exist.wav",
                sha256="a" * 64,
                canonical_sha256="b" * 64,
                duration_ms=3000,
                provenance="recorded_audio",
            )
        }
    )
    data = original.model_dump_json().encode()
    path = tmp_path / "original.json"
    path.write_bytes(data)
    notes = tmp_path / "notes.json"
    notes.write_text(json.dumps({"S01": ["user-reported possible pronunciation issue"]}))
    output = tmp_path / "replay"
    replay.main(["--record", f"S01={path}", "--output", str(output), "--annotations", str(notes)])
    result = Record.model_validate_json((output / "S01/record.json").read_text())
    assert result.audio == original.audio
    assert result.perception == original.perception
    assert result.acoustics == original.acoustics
    assert result.recording_id == original.recording_id
    assert result.intended_text == original.intended_text
    assert result.alignment.raw_response == original.alignment.raw_response
    assert result.replay["source_record_sha256"] == hashlib.sha256(data).hexdigest()
    assert result.study_annotations == ["user-reported possible pronunciation issue"]
    assert path.read_bytes() == data
    assert result.units[1].pitch.usable_frame_count == 1
    assert result.units[1].pitch.frames == original.acoustics["f0"]
    assert (output / "S01/report.md").read_text() == probe.markdown(result)
    assert replay.replay_record(original) == replay.replay_record(original)
    with pytest.raises(SystemExit):
        replay.main(["--record", f"S01={path}", "--output", str(output)])


def test_v1_record_remains_readable_and_replay_has_explicit_v2_version():
    path = (
        HERE.parents[1]
        / "docs/research/pronunciation-v2/2026-10-01-connected-speech-recon"
        / "example-guizhou/record.json"
    )
    original = Record.model_validate_json(path.read_text())
    assert original.schema_version == "connected-speech-v1"
    result = replay.replay_record(original)
    assert result.schema_version == "connected-speech-v2"
    assert result.analysis_version == "connected-probe-v2"
    assert result.replay["source_schema_version"] == original.schema_version
    assert result.perception == original.perception
    invalid = copy.deepcopy(result.model_dump())
    invalid["schema_version"] = "connected-speech-v1"
    with pytest.raises(ValidationError):
        Record.model_validate(invalid)

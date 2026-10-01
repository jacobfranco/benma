"""Structural truth-boundary tests; synthetic audio is generated only in tmp_path."""

import copy
import json
import math
import struct
import subprocess
import wave
from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from benchmark.pronunciation_v2 import connected_speech_probe as probe
from benchmark.pronunciation_v2.connected_schema import Audio, Record, Span

HERE = Path(__file__).parent


def make(text="我要去贵州", **kwargs):
    evidence = kwargs.pop("evidence", {"transcript": text, "evidence_status": "synthetic_fixture"})
    return probe.build_record(
        recording_id="test",
        audio=Audio(duration_ms=3000, provenance="synthetic_fixture"),
        provider="synthetic",
        evidence=evidence,
        raw_response={"text": text},
        **kwargs,
    )


def azure(words):
    return {"NBest": [{"Words": words}]}


def word(text, start=100, duration=600, phones=None):
    return {
        "Word": text,
        "Offset": start * 10000,
        "Duration": duration * 10000,
        "Phonemes": phones or [],
    }


def phone(label, start, duration):
    return {
        "Phoneme": label,
        "Offset": start * 10000,
        "Duration": duration * 10000,
        "PronunciationAssessment": {"AccuracyScore": 87},
    }


def test_guangzhou_guizhou_and_optional_target():
    free = make()
    targeted = make(target="我要去广州")
    assert free.perception == targeted.perception
    assert free.alignment == targeted.alignment
    assert free.text_comparison is None
    assert targeted.perception.raw_transcript == "我要去贵州"
    assert "## What Benma heard\n\n我要去贵州\n" in probe.markdown(targeted)
    substitution = next(e for e in targeted.text_comparison if e.operation == "substitution")
    assert (substitution.intended, substitution.perceived) == ("广", "贵")
    assert substitution.diagnosis == "not_inferred_from_text"
    with pytest.raises(ValidationError):
        targeted.perception.raw_transcript = "我要去广州"


@pytest.mark.parametrize(
    ("intended", "heard", "operation"),
    [
        ("买", "卖", "substitution"),
        ("我去", "我要去", "insertion"),
        ("我要去", "我去", "deletion"),
        ("我，去！", "我去", "match"),  # noqa: RUF001 -- Mandarin punctuation fixture
    ],
)
def test_text_operations(intended, heard, operation):
    assert operation in [e.operation for e in probe.compare_text(intended, heard)]


def test_ambiguous_text_alignment_abstains():
    record = make("我", target="我我")
    edit = record.units[0].target_comparison
    assert edit.correspondence == "ambiguous_minimum_edit"
    assert edit.expectation is None
    assert "target_perceived_alignment_unresolved" in record.units[0].abstention_reasons


def test_missing_timing_and_no_equal_word_split():
    record = make("贵州", azure_raw=azure([word("贵州")]))
    assert record.alignment.words[0].timing.duration_ms == 600
    assert record.alignment.words[0].syllable_timing_status == "unresolved"
    assert all(u.timing is None and u.pitch is None for u in record.units)
    assert all("no_reliable_syllable_boundary" in u.abstention_reasons for u in record.units)
    assert all(u.judgment == "INSUFFICIENT EVIDENCE" for u in record.units)


def test_sapi_mapping_and_phone_semantics():
    raw = azure([word("贵州", phones=[phone("gui4", 100, 300), phone("zhou1", 400, 300)])])
    record = make("贵州", azure_raw=raw)
    assert [u.timing.start_ms for u in record.units] == [100, 400]
    assert record.units[0].phones[0].semantics == "reference_label_not_observed_phone"
    assert record.units[0].phones[0].score is None
    assert record.alignment.raw_response == raw
    assert record.units[0].context.window.start_ms == 0
    assert record.units[1].context.previous_unit == "u0"


@pytest.mark.parametrize("labels", [["g4", "zh1"], ["guang3", "zhou1"]])
def test_phone_count_is_not_enough(labels):
    raw = azure([word("贵州", phones=[phone(labels[0], 100, 300), phone(labels[1], 400, 300)])])
    record = make("贵州", azure_raw=raw)
    assert record.units[0].timing is None


@pytest.mark.parametrize(("start", "duration"), [(-1, 500), (100, -1), (2900, 500)])
def test_invalid_spans_missing(start, duration):
    record = make("我", azure_raw=azure([word("我", start, duration)]))
    assert record.units[0].timing is None


def test_overlapping_spans_and_wrong_text_rejected():
    overlap = make("我去", azure_raw=azure([word("我", 100), word("去", 400)]))
    assert all(u.timing is None for u in overlap.units)
    conflict = make("贵州", azure_raw=azure([word("广州")]))
    assert "asr_timing_text_conflict" in conflict.alignment.issues
    assert all(u.timing is None for u in conflict.units)
    partial = make("我去", azure_raw=azure([word("我")]))
    assert all(u.timing is None for u in partial.units)


def test_native_character_tokens_and_multichar_words():
    evidence = {
        "transcript": "我贵州",
        "tokens": [
            {
                "text": "我",
                "character_start": 0,
                "character_end": 1,
                "timing": {"start_seconds": 0.1, "end_seconds": 0.3},
            },
            {
                "text": "贵州",
                "character_start": 1,
                "character_end": 3,
                "timing": {"start_seconds": 0.4, "end_seconds": 1},
            },
        ],
    }
    record = make("我贵州", evidence=evidence)
    assert record.units[0].timing.start_ms == 100
    assert record.units[1].timing is None
    assert record.alignment.words[1].timing.duration_ms == 600


def test_reading_ambiguity_and_neutral():
    assert make("行").units[0].reading.ambiguous
    assert make("行").units[0].reading.pinyin is None
    neutral = make("妈妈", target="妈妈")
    assert neutral.units[1].reading.lexical_tone == 0
    assert neutral.units[1].target_comparison.expectation.surface_tone == 0
    assert neutral.units[1].observed_tone_model is None


@pytest.mark.parametrize(
    ("text", "tone", "rule"),
    [
        ("很好", 2, "third_tone_pair"),
        ("不是", 2, "bu_before_fourth"),
        ("一个", 2, "yi_quantity"),
    ],
)
def test_existing_contextual_expectations(text, tone, rule):
    edit = probe.compare_text(text, text)[0]
    assert edit.expectation.surface_tone == tone
    assert edit.expectation.rule == rule


def test_pitch_missingness_flags_and_target_independence():
    frames = [
        {
            "timestamp_seconds": 0.1 + i * 0.02,
            "f0_hz": None if i < 7 else 150,
            "selected_f0_hz": None if i < 8 else 150,
            "energy_rms": 0.02,
            "quality_usable": i != 7,
            "voicing_probability": 0.1 if i < 7 else 0.8,
        }
        for i in range(10)
    ]
    acoustics = {"f0": frames, "energy_gate": {"threshold_rms": 0.01}}
    kwargs = {"azure_raw": azure([word("买")]), "acoustics": acoustics}
    free, targeted = make("买", **kwargs), make("买", target="卖", **kwargs)
    for field in ("pitch", "reading", "timing", "phones", "quality_flags", "observed_tone_model"):
        assert getattr(free.units[0], field) == getattr(targeted.units[0], field)
    p = free.units[0].pitch
    assert p.missing_proportion == 0.7
    assert p.active_voiced_proportion == 0.2
    assert p.frames == frames
    assert p.filtered_contour[0]["f0_hz"] is None
    assert "tracker_instability" in free.units[0].quality_flags
    assert "heavy_f0_missingness" in free.units[0].quality_flags
    assert free == make("买", **kwargs)
    assert acoustics["f0"] == frames


def test_snapshot_not_aliased_and_schema_stability():
    evidence = {"transcript": "我", "tokens": [{"text": "我"}]}
    original = copy.deepcopy(evidence)
    record = make("我", evidence=evidence)
    evidence["tokens"][0]["text"] = "你"
    assert record.perception.evidence == original
    schema = json.loads((HERE / "connected-speech-schema.json").read_text())
    assert schema == Record.model_json_schema()
    assert Record.model_validate_json(record.model_dump_json()) == record
    damaged = record.model_dump()
    damaged["alignment"]["reference_text"] = "你"
    with pytest.raises(ValidationError):
        Record.model_validate(damaged)
    with pytest.raises(ValidationError):
        Span(start_ms=100, end_ms=90, duration_ms=10)


def test_cli_outputs_same_record_and_refuses_overwrite(tmp_path):
    output = tmp_path / "result"
    arguments = [
        "--fixture",
        str(HERE / "fixtures/connected-guizhou.json"),
        "--target",
        "我要去广州",
        "--output",
        str(output),
    ]
    probe.main(arguments)
    record = Record.model_validate_json((output / "record.json").read_text())
    assert (output / "report.md").read_text() == probe.markdown(record)
    assert record.audio.sha256 is None
    assert record.audio.provenance == "synthetic_fixture"
    assert sorted(p.name for p in output.iterdir()) == ["record.json", "report.md"]
    with pytest.raises(SystemExit):
        probe.main(arguments)


def test_production_praat_and_live_ports_with_mocked_network(tmp_path, monkeypatch):
    # Signal fixture verifies plumbing/missingness; never a Mandarin gold sample.
    wav = tmp_path / "signal.wav"
    with wave.open(str(wav), "wb") as stream:
        stream.setparams((1, 2, 16000, 16000, "NONE", "not compressed"))
        stream.writeframes(
            b"".join(
                struct.pack("<h", int(5000 * math.sin(2 * math.pi * 160 * i / 16000)))
                for i in range(16000)
            )
        )
    from benma_api.speech.contracts import PerceptionEvidence, PerceptionProviderResponse

    provider = Mock(product_name="mock", request_configuration={"semantic_hints_supplied": False})
    provider.perceive.return_value = PerceptionProviderResponse(
        PerceptionEvidence("贵州", None, None, None, None, "zh", "fixture"), {"text": "贵州"}
    )
    monkeypatch.setattr(probe, "build_perception_provider", lambda _: provider)
    transport = Mock(return_value=azure([word("贵州")]))
    monkeypatch.setattr(probe, "request_azure_speech", transport)
    settings = probe.Settings(
        _env_file=None,
        perception_provider="openai",
        openai_api_key="fake",
        azure_speech_key="fake",
        azure_speech_region="test",
    )
    values = probe.run_live(wav, settings=settings, use_azure=True)
    request = provider.perceive.call_args.args[0]
    assert not hasattr(request, "target")
    assert transport.call_args.kwargs["config"]["ReferenceText"] == "贵州"
    assert values["acoustics"]["f0"]
    assert any(p["selected_f0_hz"] for p in values["acoustics"]["f0"])
    assert values["audio"].sha256
    assert set(tmp_path.iterdir()) == {wav}


def test_no_audio_staged():
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], text=True)
    assert not any(
        Path(p).suffix.lower() in {".wav", ".mp3", ".m4a", ".webm", ".flac", ".ogg"}
        for p in staged.splitlines()
    )


def test_malformed_alignment_preserves_raw_and_perception():
    raw = {"RecognitionStatus": "NoMatch", "NBest": []}
    record = make("贵州", azure_raw=raw)
    assert record.alignment.raw_response == raw
    assert record.perception.raw_transcript == "贵州"
    assert record.alignment.issues == ["malformed_alignment:ProviderMalformedResponseError"]
    assert all(u.timing is None for u in record.units)


def test_all_missing_f0_and_context_clipping():
    acoustic = {
        "f0": [
            {
                "timestamp_seconds": 0.1,
                "f0_hz": None,
                "selected_f0_hz": None,
                "quality_usable": True,
            }
        ]
    }
    record = make("我", azure_raw=azure([word("我")]), acoustics=acoustic, context_ms=5000)
    unit = record.units[0]
    assert not unit.pitch.available
    assert unit.pitch.missing_proportion == 1
    assert unit.pitch.active_voiced_proportion is None
    assert unit.context.window == Span(start_ms=0, end_ms=3000, duration_ms=3000)
    assert "insufficient_voiced_pitch" in unit.abstention_reasons


@pytest.mark.parametrize("context", [-1, float("nan"), float("inf")])
def test_invalid_context_rejected(context):
    with pytest.raises(ValueError):
        make(context_ms=context)


def test_fixture_reference_mismatch_is_rejected(tmp_path):
    fixture = tmp_path / "bad.json"
    fixture.write_text(
        json.dumps(
            {
                "duration_ms": 3000,
                "provider": "fixture",
                "evidence": {"transcript": "贵州"},
                "alignment_reference_text": "广州",
            }
        )
    )
    with pytest.raises(SystemExit):
        probe.main(["--fixture", str(fixture), "--output", str(tmp_path / "out")])
    assert not (tmp_path / "out").exists()


def test_schema_rejects_unlabeled_model_and_audio_boundaries():
    record = make("我", azure_raw=azure([word("我")]))
    invalid = record.model_dump()
    invalid["units"][0]["observed_tone_model"] = {
        "prediction": 1,
        "probabilities": [0.7, 0.1, 0.1, 0.1],
    }
    with pytest.raises(ValidationError):
        Record.model_validate(invalid)
    invalid = record.model_dump()
    invalid["units"][0]["timing"] = {"start_ms": 100, "end_ms": 3100, "duration_ms": 3000}
    with pytest.raises(ValidationError):
        Record.model_validate(invalid)

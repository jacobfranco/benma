"""Product regressions over saved timing fixtures and synthetic F0; no provider calls."""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path
from unittest.mock import Mock

import pytest
from test_perceived_speech import perception_for

from benma_api.db.models import AcousticRun, PerceptionRun
from benma_api.pronunciation.alignment import AlignmentResponse
from benma_api.pronunciation.azure_alignment import AzureSpeechAligner, azure_grapheme_units
from benma_api.pronunciation.contours import display_contour, syllable_contour
from benma_api.pronunciation.perceived import (
    PerceivedSpeechAnalysisService,
    analysis_response,
    perceived_syllables,
)
from benma_api.pronunciation.tone_graph import sentence_pitch_evidence
from benma_api.schemas import DisplayContour, DisplayPitchPoint


def test_adjacent_qu_ba_half_open_ownership_keeps_final_endpoint_in_timeline():
    syllables = perceived_syllables("去吧", {})
    for s, start, end in zip(syllables, [0, 0.1], [0.1, 0.2], strict=True):
        s.start_seconds, s.end_seconds = start, end
    times = [0, 0.09, 0.1, 0.11, 0.19, 0.2]
    raw = [{"timestamp_seconds": t, "f0_hz": 200} for t in times]
    before = copy.deepcopy(raw)
    display = DisplayContour(
        baseline_hz=200,
        segments=[[DisplayPitchPoint(timestamp_seconds=t, normalized_semitones=0) for t in times]],
    )
    graph = sentence_pitch_evidence(raw, display, syllables)
    assert [[p.timestamp_seconds for p in s] for s in graph.filtered.segments] == [
        [0, 0.09],
        [0.1, 0.11, 0.19],
        [0.2],
    ]
    owned = [
        [
            p.timestamp_seconds
            for seg in syllable_contour(graph.filtered, a, b).segments
            for p in seg
        ]
        for a, b in [(0, 0.1), (0.1, 0.2)]
    ]
    assert owned == [[0, 0.09], [0.1, 0.11, 0.19]]
    assert set(owned[0]).isdisjoint(owned[1])
    assert graph.raw[-1].timestamp_seconds == graph.mine.segments[-1][0].timestamp_seconds == 0.2
    assert raw == before


def test_t3_chain_keeps_lexical_identity_when_prosodic_grouping_is_unresolved():
    syllables = perceived_syllables("我想买五把雨伞。", {})
    known = [s for s in syllables if s.characters != "把"]
    assert all(s.lexical_tone == 3 and s.pinyin for s in known)
    # Existing reading policy abstains for polyphonic 把; do not invent a rule.
    assert syllables[4].reading_source == "unresolved"
    assert syllables[4].lexical_tone is None
    assert all(s.expected_surface_tone is None for s in syllables)


@pytest.mark.parametrize(
    "text,character,tone",
    [
        ("这不是我的。", "不", 2),
        ("我要一个苹果。", "一", 2),
        ("我们去吧。", "们", 0),
        ("我们去吧。", "吧", 0),
    ],
)
def test_preserved_contextual_references(text, character, tone):
    syllable = next(s for s in perceived_syllables(text, {}) if s.characters == character)
    assert syllable.expected_surface_tone == tone


def raw_pitch():
    return [
        {
            "timestamp_seconds": i / 100,
            "f0_hz": 180 + i if i < 6 or i >= 11 else None,
            "tracker_f0_hz": 180 + i,
            "selected_f0_hz": 180 + i if i < 6 or i >= 11 else None,
            "quality_usable": True,
            "voicing_probability": 0.9,
        }
        for i in range(15)
    ]


def test_raw_selected_display_are_separate_deterministic_and_do_not_fill_gaps():
    raw = raw_pitch()
    before = copy.deepcopy(raw)
    syllables = perceived_syllables("你好啊", {})
    for s, start, end in zip(syllables, [0, 0.06, 0.11], [0.06, 0.11, 0.15], strict=True):
        s.start_seconds, s.end_seconds = start, end
    display = display_contour(raw)
    graph = sentence_pitch_evidence(raw, display, syllables)
    assert graph == sentence_pitch_evidence(raw, display, syllables)
    assert raw == before
    assert len(graph.filtered.segments) == len(graph.mine.segments) == 2
    assert len(graph.filtered.segments[0]) == 6
    assert len(graph.filtered.segments[1]) == 4
    assert not any(0.06 <= p.timestamp_seconds < 0.11 for s in graph.mine.segments for p in s)
    assert sum(p.retained for p in graph.raw) == 10
    assert all(p.tracker_f0_hz is not None for p in graph.raw)
    for segment in graph.filtered.segments:
        for p in segment:
            hz = next(r["f0_hz"] for r in raw if r["timestamp_seconds"] == p.timestamp_seconds)
            assert p.normalized_semitones == 12 * math.log2(hz / graph.filtered.baseline_hz)
    # Contextual expectation/observed classifier fields are never a geometry input.
    for s in syllables:
        s.expected_surface_tone = 0
        s.lexical_tone = None
        s.pinyin = None
        s.observed_contour.classification = "4-like"
    assert sentence_pitch_evidence(raw, display, syllables) == graph


def test_all_missing_and_single_syllable_keep_empty_or_measured_contour():
    raw = [{"timestamp_seconds": i / 100, "f0_hz": None} for i in range(20)]
    graph = sentence_pitch_evidence(raw, display_contour(raw), perceived_syllables("吗", {}))
    assert graph.filtered.segments == graph.mine.segments == []
    assert not any(p.retained for p in graph.raw)
    graph = sentence_pitch_evidence(raw_pitch(), display_contour(raw_pitch()), [])
    assert len(graph.filtered.segments) == 2  # Untimed text does not erase measured F0.


def grapheme_word(text="行吗"):
    return {
        "NBest": [
            {
                "Words": [
                    {
                        "Word": text,
                        "Offset": 0,
                        "Duration": 1_500_000,
                        "Syllables": [
                            {"Grapheme": c, "Offset": i * 750_000, "Duration": 750_000}
                            for i, c in enumerate(text)
                        ],
                        "Phonemes": [{"Phoneme": "incorrect 1"}],
                    }
                ]
            }
        ]
    }


def test_production_grapheme_mapping_is_reading_and_score_independent():
    raw = grapheme_word()
    before = copy.deepcopy(raw)
    units = azure_grapheme_units(raw, "行吗。")
    assert [u["label"] for u in units] == list("行吗")
    assert [u["start_seconds"] for u in units] == [0, 0.075]
    assert all(u["source"] == "azure_provider_grapheme" for u in units)
    assert raw == before
    assert azure_grapheme_units(raw, "行吧。") == []
    word = raw["NBest"][0]["Words"][0]
    word["Syllables"][1].pop("Duration")
    assert len(azure_grapheme_units(raw, "行吗")) == 1
    word["Syllables"][1]["Grapheme"] = "马"
    assert azure_grapheme_units(raw, "行吗") == []
    word.pop("Syllables")
    assert azure_grapheme_units(raw, "行吗") == []  # Never substitute phone counts.


@pytest.mark.parametrize("mutation", ["overlap", "outside", "omission", "insertion", "extra"])
def test_malformed_grapheme_tier_abstains(mutation):
    raw = grapheme_word()
    word = raw["NBest"][0]["Words"][0]
    if mutation == "overlap":
        word["Syllables"][1]["Offset"] = 10
    elif mutation == "outside":
        word["Syllables"][1]["Duration"] = 9_000_000
    elif mutation in {"omission", "insertion"}:
        word["PronunciationAssessment"] = {"ErrorType": mutation.title()}
    else:
        word["Syllables"].append(word["Syllables"][0])
    assert azure_grapheme_units(raw, "行吗") == []


def test_saved_36_grapheme_spans_and_s13_guizhou_identity():
    fixture = Path(__file__).resolve().parents[3] / (
        "benchmark/pronunciation_v2/fixtures/connected-real-mapping-excerpts.json"
    )
    captures = json.loads(fixture.read_text())["captures"]
    count = 0
    for capture in captures:
        raw, text = capture["azure_raw"], capture["perceived_text"]
        units = azure_grapheme_units(raw, text)
        count += len(units)
        assert "".join(u["label"] for u in units) == "".join(c for c in text if c.isalnum())
        if capture["study_id"] == "S13":
            assert text == "我要去贵州。"
            assert "".join(u["label"] for u in units) == "我要去贵州"
            assert azure_grapheme_units(raw, "我要去广州。") == []
            gui = perceived_syllables(text, {})[3]
            assert (gui.characters, gui.pinyin, gui.expected_surface_tone) == ("贵", "guì", 4)
    assert count == 36


def test_api_preserves_ambiguous_timed_character_and_raw_measurements(
    uploaded_utterance, session_factory, settings, store, monkeypatch
):
    perception = perception_for(session_factory, uploaded_utterance, "行吗。")
    raw = raw_pitch()
    analyzer = Mock(algorithm_name="fixture", algorithm_version="1", parameters={})
    analyzer.analyze.return_value = {"f0": raw, "mobile_f0": raw}
    request = Mock(return_value=grapheme_word())
    monkeypatch.setattr("benma_api.pronunciation.azure_alignment.request_azure_speech", request)
    with session_factory() as db:
        run = PerceivedSpeechAnalysisService(
            db, store, settings, analyzer=analyzer, aligner=AzureSpeechAligner("fixture", "fixture")
        ).run(account_id=perception.account_id, perception_run_id=perception.id)
        data = analysis_response(run).data
        s = data.syllables[0]
        assert (s.characters, s.pinyin, s.expected_surface_tone) == ("行", None, None)
        assert (s.start_seconds, s.end_seconds) == (0, 0.075)
        assert data.tone_graph.mine.segments
        assert data.tone_graph.filtered.segments
        assert db.get(AcousticRun, run.acoustic_run_id).normalized_result["f0"] == raw
        assert db.get(PerceptionRun, perception.id).transcript == "行吗。"
        assert request.call_args.kwargs["config"]["ReferenceText"] == "行吗。"
        assert run.result["timing_evidence"]["provider_timing"] == grapheme_word()


def test_partial_alignment_does_not_fabricate_remaining_timing(
    uploaded_utterance, session_factory, settings, store
):
    perception = perception_for(session_factory, uploaded_utterance, "行吗")
    raw = raw_pitch()
    analyzer = Mock(algorithm_name="fixture", algorithm_version="1", parameters={})
    analyzer.analyze.return_value = {"f0": raw, "mobile_f0": raw}
    aligner = Mock(algorithm_name="fixture", algorithm_version="1")
    aligner.align.return_value = AlignmentResponse(
        units=azure_grapheme_units(grapheme_word(), "行吗")[:1],
        raw_result={},
        evidence_status="live_provider",
    )
    with session_factory() as db:
        run = PerceivedSpeechAnalysisService(
            db, store, settings, analyzer=analyzer, aligner=aligner
        ).run(account_id=perception.account_id, perception_run_id=perception.id)
        data = analysis_response(run).data
        assert data.alignment_status == "partial"
        assert data.syllables[0].start_seconds == 0
        assert data.syllables[1].start_seconds is None
        assert data.tone_graph.filtered.segments[-1][-1].timestamp_seconds == 0.14


def test_old_saved_analysis_contract_remains_readable():
    # The additive field defaults to unavailable; older records are never rewritten.
    from benma_api.schemas import PerceivedAnalysisData

    assert PerceivedAnalysisData.model_fields["tone_graph"].default is None


@pytest.mark.parametrize(
    "raw", [{}, {"NBest": None}, {"NBest": 1}, {"NBest": [None]}, {"NBest": [{}]}]
)
def test_malformed_provider_envelope_abstains(raw):
    assert azure_grapheme_units(raw, "水果") == []


def test_grapheme_mapping_rejects_word_audio_overflow_and_cross_word_overlap():
    raw = grapheme_word("水果")
    assert len(azure_grapheme_units(raw, "水果", duration_seconds=0.15)) == 2
    assert azure_grapheme_units(raw, "水果", duration_seconds=0.14) == []
    word = raw["NBest"][0]["Words"][0]
    word["Phonemes"] = None  # A broken phone tier cannot erase independent timing.
    assert len(azure_grapheme_units(raw, "水果", duration_seconds=0.15)) == 2
    raw["NBest"][0]["Words"].append(copy.deepcopy(word))
    assert azure_grapheme_units(raw, "水果水果") == []


@pytest.mark.parametrize("invalid", [0, -1, True, float("inf"), float("nan")])
def test_invalid_grapheme_duration_leaves_only_valid_units(invalid):
    raw = grapheme_word()
    raw["NBest"][0]["Words"][0]["Syllables"][0]["Duration"] = invalid
    units = azure_grapheme_units(raw, "行吗")
    assert [u["label"] for u in units] == ["吗"]


def test_rejected_tracker_points_never_reappear_in_mine_or_filtered():
    raw = raw_pitch()
    raw[3]["quality_usable"] = False
    raw[3]["selected_f0_hz"] = None
    graph = sentence_pitch_evidence(raw, display_contour(raw), [])
    assert graph.raw[3].tracker_f0_hz == 183
    assert graph.raw[3].retained is False
    assert len(graph.mine.segments) == 3
    assert not any(
        p.timestamp_seconds == 0.03 for segment in graph.filtered.segments for p in segment
    )


def test_both_graphemes_keep_timing_when_both_readings_abstain(
    uploaded_utterance, session_factory, settings, store, monkeypatch
):
    perception = perception_for(session_factory, uploaded_utterance, "水果")
    monkeypatch.setattr(
        "benma_api.pronunciation.perceived.resolve_run",
        lambda _: [(None, "unresolved", []), (None, "unresolved", [])],
    )
    monkeypatch.setattr(
        "benma_api.pronunciation.azure_alignment.request_azure_speech",
        lambda **_: grapheme_word("水果"),
    )
    analyzer = Mock(algorithm_name="fixture", algorithm_version="1", parameters={})
    analyzer.analyze.return_value = {"f0": raw_pitch(), "mobile_f0": raw_pitch()}
    with session_factory() as db:
        run = PerceivedSpeechAnalysisService(
            db, store, settings, analyzer=analyzer, aligner=AzureSpeechAligner("fixture", "fixture")
        ).run(account_id=perception.account_id, perception_run_id=perception.id)
        data = analysis_response(run).data
        assert [(s.characters, s.start_seconds, s.end_seconds) for s in data.syllables] == [
            ("水", 0, 0.075),
            ("果", 0.075, 0.15),
        ]
        assert all(s.pinyin is None and s.expected_surface_tone is None for s in data.syllables)
        assert data.tone_graph.filtered.segments


def test_attrition_diagnostics_explain_rejections_without_changing_selection():
    raw = [
        {
            "timestamp_seconds": i / 100,
            "f0_hz": 200,
            "tracker_f0_hz": 200,
            "voicing_probability": 0.9,
            "quality_usable": True,
        }
        for i in range(30)
    ]
    raw[0].update(f0_hz=None, tracker_f0_hz=None)
    raw[1].update(f0_hz=None, energy_gated=True)
    raw[2].update(quality_usable=False, selection_reason="low_frequency_contamination")
    raw[3].update(voicing_probability=0.2)
    raw[15].update(f0_hz=400, tracker_f0_hz=400)
    before = copy.deepcopy(raw)
    diagnostics = []
    expected = display_contour(raw)
    assert display_contour(raw, diagnostics=diagnostics) == expected
    assert raw == before and len(diagnostics) == len(raw)
    assert "tracker_missing" in diagnostics[0]["reasons"]
    assert "below_energy_gate" in diagnostics[1]["reasons"]
    assert "low_frequency_contamination" in diagnostics[2]["reasons"]
    assert "weak_periodicity" in diagnostics[3]["reasons"]
    assert "bracketed_short_pitch_island" in diagnostics[15]["reasons"]
    assert "local_hampel_outlier" in diagnostics[15]["reasons"]
    assert all(d["retained"] == (i not in {0, 1, 2, 3, 15}) for i, d in enumerate(diagnostics))


def test_punctuation_never_consumes_character_cells():
    syllables = perceived_syllables("我，想买五把雨伞。", {})  # noqa: RUF001
    assert "".join(s.characters for s in syllables) == "我想买五把雨伞"
    assert len(syllables) == 7
    assert [s.character_start for s in syllables] == [0, 2, 3, 4, 5, 6, 7]


def test_latest_umbrella_anonymous_syllables_cannot_be_assigned_by_phone_or_order():
    # Exact timing-only excerpt from perception 1a927887-320c-4f15-876e-60648b472c8c.
    raw = {
        "NBest": [
            {
                "Words": [
                    {
                        "Word": "雨伞",
                        "Offset": 33200000,
                        "Duration": 9900000,
                        "Syllables": [
                            {"Syllable": "", "Offset": 33200000, "Duration": 4300000},
                            {"Syllable": "", "Offset": 37600000, "Duration": 5500000},
                        ],
                        "Phonemes": [
                            {"Phoneme": "yu 2", "Offset": 33200000, "Duration": 4300000},
                            {"Phoneme": "san 3", "Offset": 37600000, "Duration": 5500000},
                        ],
                    }
                ]
            }
        ]
    }
    before = copy.deepcopy(raw)
    assert azure_grapheme_units(raw, "雨伞", duration_seconds=4.4118125) == []
    assert raw == before
    # Only explicit character attribution would make these boundaries recoverable.
    for entry, character in zip(raw["NBest"][0]["Words"][0]["Syllables"], "雨伞", strict=True):
        entry["Grapheme"] = character
    units = azure_grapheme_units(raw, "雨伞", duration_seconds=4.4118125)
    assert [(u["label"], u["start_seconds"], u["end_seconds"]) for u in units] == [
        ("雨", 3.32, 3.75),
        ("伞", 3.76, 4.31),
    ]


@pytest.mark.parametrize("tone", [1, 2, 3, 4])
def test_primary_only_abstains_with_valid_timing_and_no_raw_pitch(tone):
    syllables = perceived_syllables("贵州", {})
    for i, s in enumerate(syllables):
        s.start_seconds, s.end_seconds = i * 0.2, (i + 1) * 0.2
        s.expected_surface_tone = tone
    raw = [{"timestamp_seconds": i / 100, "f0_hz": None, "tracker_f0_hz": None} for i in range(40)]
    graph = sentence_pitch_evidence(raw, display_contour(raw), syllables)
    assert graph.mine.segments == graph.filtered.segments == []
    assert not any(p.retained or p.tracker_f0_hz for p in graph.raw)
    assert "".join(s.characters for s in syllables) == "贵州"


def test_unsupported_high_branch_stays_raw_and_short_gaps_stay_unbridged():
    raw = [
        {
            "timestamp_seconds": t,
            "f0_hz": hz,
            "tracker_f0_hz": hz,
            "voicing_probability": 0.8,
            "quality_usable": True,
        }
        for t, hz in [
            (1.2027, 134.611),
            (1.2127, None),
            (1.2227, 476.266),
            (1.2327, 467.038),
            (1.2427, 462.807),
        ]
    ]
    unit = perceived_syllables("州", {})[0]
    unit.start_seconds, unit.end_seconds = 1.06, 1.6
    graph = sentence_pitch_evidence(raw, display_contour(raw), [unit])
    assert [p.tracker_f0_hz for p in graph.raw] == [134.611, None, 476.266, 467.038, 462.807]
    assert len(graph.mine.segments) == len(graph.filtered.segments) == 2
    assert all(p.timestamp_seconds != 1.2127 for s in graph.mine.segments for p in s)

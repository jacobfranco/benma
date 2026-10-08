"""Semantic presentation without new classification, providers or user audio."""

from __future__ import annotations

import copy
from unittest.mock import Mock

import pytest
from test_perceived_speech import perception_for

from benma_api.pronunciation.alignment import AlignmentResponse
from benma_api.pronunciation.azure_alignment import azure_grapheme_units, azure_word_timing_groups
from benma_api.pronunciation.contours import classify_contour, display_contour
from benma_api.pronunciation.perceived import (
    PerceivedSpeechAnalysisService,
    analysis_response,
    perceived_syllables,
)
from benma_api.pronunciation.tone_graph import sentence_pitch_evidence


def word_payload():
    return {
        "NBest": [
            {
                "Words": [
                    {
                        "Word": "雨伞",
                        "Offset": 0,
                        "Duration": 1_500_000,
                        # Deliberately unequal anonymous intervals: never assigned by position.
                        "Syllables": [
                            {"Offset": 0, "Duration": 400_000},
                            {"Offset": 500_000, "Duration": 1_000_000},
                        ],
                        "Phonemes": [{"Phoneme": "yu 2"}, {"Phoneme": "san 3"}],
                    }
                ]
            }
        ]
    }


def groups(raw=None, text="雨伞", syllables=None, duration=0.15):
    return azure_word_timing_groups(
        word_payload() if raw is None else raw,
        text,
        perceived_syllables(text, {}) if syllables is None else syllables,
        duration_seconds=duration,
        timing_evidence_id="saved-evidence",
    )


@pytest.mark.parametrize("text,reference,gesture", [("贵", 4, "dipping"), ("州", 1, "falling")])
def test_character_reference_and_observation_coexist_without_mutation(text, reference, gesture):
    raw = [
        {
            "timestamp_seconds": i / 100,
            "f0_hz": 200
            * 2 ** (((abs(i - 20) / 20 * 6) if gesture == "dipping" else (6 - i / 40 * 6)) / 12),
            "voicing_probability": 0.95,
        }
        for i in range(41)
    ]
    before = copy.deepcopy(raw)
    contour = display_contour(raw)
    observation = classify_contour(contour, 0, 0.41, raw=raw)
    s = perceived_syllables(text, {})[0]
    s.start_seconds, s.end_seconds = 0, 0.41
    s.observed_contour = observation
    assert (s.characters, s.expected_surface_tone, s.observed_gesture) == (text, reference, gesture)
    assert s.observed_confidence == "moderate"
    original = s.observed_gesture
    for tone in [None, 0, 1, 2, 3, 4]:
        s.lexical_tone = tone
        s.expected_surface_tone = tone
        assert s.observed_gesture == original
        assert classify_contour(contour, 0, 0.41, raw=raw) == observation
    assert raw == before
    assert "detected_tone" not in s.model_dump()


def test_group_has_exact_word_span_no_character_pitch_or_internal_boundary():
    raw = word_payload()
    before = copy.deepcopy(raw)
    syllables = perceived_syllables("雨伞", {})
    result = groups(raw, syllables=syllables)
    assert len(result) == 1
    assert result[0].model_dump(exclude={"pitch_projection", "pitch_eligibility"}) == {
        "text": "雨伞",
        "character_start": 0,
        "character_end": 2,
        "start_seconds": 0,
        "end_seconds": 0.15,
        "source": "azure_word",
        "timing_evidence_id": "saved-evidence",
    }
    assert azure_grapheme_units(raw, "雨伞") == []
    assert all(s.start_seconds is None and s.display_contour is None for s in syllables)
    assert all(s.observed_gesture == "unclear" for s in syllables)
    assert raw == before


@pytest.mark.parametrize("error", ["Omission", "Insertion"])
def test_group_rejects_inserted_or_omitted_words(error):
    raw = word_payload()
    raw["NBest"][0]["Words"][0]["PronunciationAssessment"] = {"ErrorType": error}
    assert groups(raw) == []


@pytest.mark.parametrize("duration", [0, -1, True, float("nan"), float("inf")])
def test_group_rejects_invalid_word_timing(duration):
    raw = word_payload()
    raw["NBest"][0]["Words"][0]["Duration"] = duration
    assert groups(raw) == []


def test_group_rejects_mismatch_overflow_overlap_noncontiguous_and_partial_attribution():
    assert groups(text="水果") == []
    assert groups(duration=0.14) == []
    assert groups(text="雨,伞") == []
    raw = word_payload()
    raw["NBest"][0]["Words"] *= 2
    assert groups(raw, text="雨伞雨伞") == []
    syllables = perceived_syllables("雨伞", {})
    syllables[0].start_seconds, syllables[0].end_seconds = 0, 0.04
    assert groups(syllables=syllables) == []


def test_group_geometry_preserves_raw_time_and_only_splits_at_word_edges():
    raw = [{"timestamp_seconds": i / 100, "f0_hz": 200 + i} for i in range(20)]
    before = copy.deepcopy(raw)
    graph = sentence_pitch_evidence(
        raw, display_contour(raw), perceived_syllables("雨伞", {}), groups()
    )
    assert [[p.timestamp_seconds for p in seg] for seg in graph.filtered.segments] == [
        [i / 100 for i in range(15)],
        [i / 100 for i in range(15, 20)],
    ]
    assert [p.timestamp_seconds for p in graph.raw] == [p["timestamp_seconds"] for p in raw]
    assert raw == before


def test_api_group_persistence_and_old_response_enrichment_use_only_saved_evidence(
    uploaded_utterance,
    session_factory,
    settings,
    store,
):
    perception = perception_for(session_factory, uploaded_utterance, "雨伞")
    raw = [{"timestamp_seconds": i / 100, "f0_hz": 200 + i} for i in range(15)]
    analyzer = Mock(algorithm_name="fixture", algorithm_version="1", parameters={})
    analyzer.analyze.return_value = {"f0": raw, "mobile_f0": raw}
    aligner = Mock(algorithm_name="azure_speech_alignment_only", algorithm_version="fixture")
    aligner.align.return_value = AlignmentResponse(
        units=[], raw_result=word_payload(), evidence_status="live_provider"
    )
    with session_factory() as db:
        run = PerceivedSpeechAnalysisService(
            db, store, settings, analyzer=analyzer, aligner=aligner
        ).run(
            account_id=perception.account_id,
            perception_run_id=perception.id,
        )
        assert len(run.result["timing_groups"]) == 1
        response = analysis_response(run)
        assert response.data.tone_graph.filtered.segments
        assert all(s.start_seconds is None for s in response.data.syllables)
        # A pre-pass saved row receives the same group, without mutating JSON or
        # calling alignment/acoustics while serializing the response.
        run.result = {k: v for k, v in run.result.items() if k != "timing_groups"}
        before = copy.deepcopy(run.result)
        historical = analysis_response(run).data.timing_groups
        assert [
            g.model_dump(exclude={"pitch_projection", "pitch_eligibility"}) for g in historical
        ] == [
            g.model_dump(exclude={"pitch_projection", "pitch_eligibility"})
            for g in response.data.timing_groups
        ]
        assert historical[0].pitch_projection is None
        assert (
            response.data.timing_groups[0].pitch_projection.track_evidence_id
            == response.data.pitch_track_evidence_id
        )
        assert response.data.timing_groups[0].pitch_projection.frame_indices == tuple(range(15))
        assert all(s.pitch_projection is None for s in response.data.syllables)
        assert run.result == before
        assert aligner.align.call_count == analyzer.analyze.call_count == 1
        run.result = {**run.result, "alignment_status": "synthetic"}
        assert analysis_response(run).data.timing_groups == []

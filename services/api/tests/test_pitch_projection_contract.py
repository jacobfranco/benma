"""Projection regressions; only saved evidence and deterministic numeric fixtures."""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import pytest

from benma_api.pronunciation.azure_alignment import azure_grapheme_units
from benma_api.pronunciation.pitch_evidence import project_pitch
from benma_api.pronunciation.pitch_types import UtterancePitchTrack
from benma_api.schemas import PerceivedAnalysisData

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures/pitch_projection_89cee47e.json").read_text()
)


def test_physical_take_serialization_preserves_every_selected_source_index():
    track = UtterancePitchTrack.model_validate(FIXTURE["track"])
    data = PerceivedAnalysisData.model_validate(FIXTURE["data"])
    data = PerceivedAnalysisData.model_validate_json(data.model_dump_json())
    by_time = {f.timestamp_seconds: i for i, f in enumerate(track.frames)}
    owned = set()
    for s in data.syllables:
        region = project_pitch(
            track,
            s.start_seconds,
            s.end_seconds,
            timing_source=s.timing_source,
            timing_evidence_id=s.timing_evidence_id,
        )
        assert region == s.pitch_projection
        assert not owned.intersection(region.frame_indices)
        owned.update(region.frame_indices)
        displayed = [
            p
            for seg in data.tone_graph.filtered.segments
            for p in seg
            if s.start_seconds <= p.timestamp_seconds < s.end_seconds
        ]
        assert [by_time[p.timestamp_seconds] for p in displayed] == [
            i for i in region.frame_indices if track.frames[i].selected_f0_hz is not None
        ]
        for p in displayed:
            frame = track.frames[by_time[p.timestamp_seconds]]
            assert p.normalized_semitones == pytest.approx(
                12 * math.log2(frame.selected_f0_hz / track.baseline_hz)
            )


def test_physical_zhe_second_fragment_is_inside_zhe_and_ge_was_energy_excluded():
    track = UtterancePitchTrack.model_validate(FIXTURE["track"])
    zhe, ge = FIXTURE["data"]["syllables"][-2:]
    assert (zhe["start_seconds"], zhe["end_seconds"]) == (2.34, 2.73)
    assert (ge["start_seconds"], ge["end_seconds"]) == (2.74, 3.04)
    selected = [
        i for i in zhe["pitch_projection"]["frame_indices"] if track.frames[i].selected_f0_hz
    ]
    assert selected == [*range(245, 260), *range(263, 268)]
    assert track.frames[267].timestamp_seconds == 2.7004
    raw_ge = [i for i in ge["pitch_projection"]["frame_indices"] if track.frames[i].raw_f0_hz]
    assert raw_ge == list(range(291, 299))
    assert all(track.frames[i].selected_f0_hz is None for i in raw_ge)
    assert all("below_energy_gate" in track.frames[i].exclusion_reasons for i in raw_ge)
    assert ge["pitch_eligibility"]["state"] == "insufficient"


def test_adjacent_distinct_contours_gap_boundary_and_group_never_steal_frames():
    # Immutable synthetic evidence: falling A, gap, rising B, exact shared endpoint.
    payload = copy.deepcopy(FIXTURE["track"])
    payload.update(evidence_id="deterministic-projection-control", duration_seconds=1.0)
    payload["frames"] = [
        {
            "timestamp_seconds": i / 100,
            "raw_f0_hz": 150 * 2 ** ((-i if i < 30 else i - 60) / 100),
            "selected_f0_hz": None
            if 30 <= i < 60
            else 150 * 2 ** ((-i if i < 30 else i - 60) / 100),
        }
        for i in range(101)
    ]
    track = UtterancePitchTrack.model_validate(payload)
    before = track.model_dump_json()
    a = project_pitch(track, 0, 0.5, timing_source="accepted", timing_evidence_id="same")
    b = project_pitch(track, 0.5, 1, timing_source="accepted", timing_evidence_id="same")
    assert a.frame_indices == tuple(range(50))
    assert b.frame_indices == tuple(range(50, 100))
    assert [i for i in a.frame_indices if track.frames[i].selected_f0_hz] == list(range(30))
    assert [i for i in b.frame_indices if track.frames[i].selected_f0_hz] == list(range(60, 100))
    assert 100 not in b.frame_indices
    group = project_pitch(track, 0, 1, timing_source="azure_word")
    assert group.frame_indices == tuple(range(100))
    for source in (None, "synthetic", "equal_split"):
        assert not project_pitch(track, None, None, timing_source=source).frame_indices
    assert track.model_dump_json() == before


@pytest.mark.parametrize("boundary", [0.5, 0.5004, 0.50000001, 0.49999999])
def test_fractional_boundaries_preserve_source_seconds_without_rounding(boundary):
    payload = copy.deepcopy(FIXTURE["track"])
    payload.update(evidence_id="fractional-boundary-control", duration_seconds=1.0)
    times = [boundary - 1e-8, boundary, boundary + 1e-8, 1.0]
    payload["frames"] = [dict(timestamp_seconds=t, raw_f0_hz=150) for t in times]
    track = UtterancePitchTrack.model_validate(payload)
    a = project_pitch(track, 0, boundary, timing_source="accepted")
    b = project_pitch(track, boundary, 1, timing_source="accepted")
    assert a.frame_indices == (0,)
    assert b.frame_indices == (1, 2)
    assert not set(a.frame_indices) & set(b.frame_indices)


def test_latest_physical_pattern_already_exists_in_raw_frames_and_provider_global_spans():
    saved = json.loads(
        (Path(__file__).parent / "fixtures/pitch_measurement_430fcc2e.json").read_text()
    )
    data = PerceivedAnalysisData.model_validate(saved["data"])
    timing = saved["data"]["timing_evidence"]
    mapped = azure_grapheme_units(
        timing["provider_timing"],
        saved["alignment_reference_text"],
        duration_seconds=data.duration_seconds,
    )
    # Provider offsets are already recording-global 100 ns ticks. Neither the
    # response Offset nor the word Offset is added to a grapheme a second time.
    assert (
        [(u["start_seconds"], u["end_seconds"]) for u in mapped]
        == [(s.start_seconds, s.end_seconds) for s in data.syllables]
        == [(0.58, 0.91), (0.92, 1.19), (1.2, 1.47), (1.48, 1.79), (1.8, 2.25)]
    )
    for s, count in zip(data.syllables, [21, 22, 3, 15, 18], strict=True):
        raw = [
            p for p in data.tone_graph.raw if s.start_seconds <= p.timestamp_seconds < s.end_seconds
        ]
        displayed = [
            p
            for seg in data.tone_graph.filtered.segments
            for p in seg
            if s.start_seconds <= p.timestamp_seconds < s.end_seconds
        ]
        assert len(displayed) == count
        assert [p.timestamp_seconds for p in displayed] == [
            p.timestamp_seconds for p in raw if p.retained
        ]
        assert all(p.source_frame_index in s.pitch_projection.frame_indices for p in raw)
    mai = [p for p in data.tone_graph.raw if 1.2 <= p.timestamp_seconds < 1.47]
    assert sum(p.tracker_f0_hz is not None for p in mai) == 3
    assert sum("tracker_missing" in p.exclusion_reasons for p in mai) == 24

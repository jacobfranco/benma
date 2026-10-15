"""Offline candidate/state regressions; no audio, provider or database dependency."""

import copy
import json
from pathlib import Path

import pytest

from benchmark.pronunciation_v2.raw_tracker_audit import frame_diagnostic, summarize_frames

FIXTURE = json.loads(
    (
        Path(__file__).resolve().parents[2]
        / "services/api/tests/fixtures/raw_tracker_mai_430fcc2e.json"
    ).read_text()
)


def test_physical_mai_candidates_exist_but_estimator_path_is_already_unvoiced():
    before = copy.deepcopy(FIXTURE)
    frames = [frame_diagnostic(f["point"], f["retained"]) for f in FIXTURE["frames"]]
    report = summarize_frames(frames, 1.2, 1.47)
    assert report == FIXTURE["expected_summary"]
    assert report["total_frames"] == 27
    assert report["states"] == {"retained": 3, "estimator_unvoiced_with_candidates": 24}
    assert report["raw"]["voiced_frames"] == report["retained"]["voiced_frames"] == 3
    assert report["raw"]["longest_unvoiced_run_seconds"] == 0.24
    assert all(f["candidate_count"] > 0 for f in frames)
    # Zero strength is the selected unvoiced candidate, not the strongest available
    # autocorrelation peak, and 'praat_selected' alone is not a voiced decision.
    unvoiced = [f for f in frames if f["raw_f0_hz"] is None]
    assert all(
        f["selected_strength"] == 0 and f["best_candidate"]["strength"] > 0 for f in unvoiced
    )
    assert all(not f["energy_gated"] for f in frames)
    assert any(f["saved_selection_reason"] == "praat_selected" for f in unvoiced)
    assert before == FIXTURE


def test_saved_replay_distinguishes_local_voicing_from_estimator_continuity():
    scores = FIXTURE["replayed_local_scores"][3:]
    assert len(scores) == 24
    assert all(f["praat_intensity"] > 0.03 for f in scores)
    assert all(f["unvoiced_local_score"] == 0.45 for f in scores)
    locally_voiced = [
        f["timestamp_seconds"]
        for f in scores
        if f["best_voiced_local_score"] > f["unvoiced_local_score"]
    ]
    assert locally_voiced == [1.232, 1.262, 1.272]
    assert FIXTURE["replay"]["all_f0_fields_equal"] is True
    assert FIXTURE["replay"]["frame_count"] == 322


@pytest.mark.parametrize(
    "reason",
    [
        "below_energy_gate",
        "weak_periodicity",
        "local_hampel_outlier",
        "low_frequency_contamination",
        "bracketed_short_pitch_island",
    ],
)
def test_diagnostic_separates_benma_rejection_of_voiced_output_from_estimator_unvoicing(reason):
    original = copy.deepcopy(FIXTURE["frames"][0])
    original["retained"].update(selected_f0_hz=None, exclusion_reasons=[reason])
    frame = frame_diagnostic(original["point"], original["retained"])
    assert frame["state"] == "benma_rejected_voiced_output"
    assert frame["raw_f0_hz"] > 0
    assert frame["exclusion_reasons"] == [reason]


def test_absent_candidate_history_is_not_reported_as_estimator_failure():
    original = copy.deepcopy(FIXTURE["frames"][3])
    original["point"].pop("pitch_candidates")
    assert (
        frame_diagnostic(original["point"], original["retained"])["state"]
        == "candidate_history_unavailable"
    )
    original["point"]["pitch_candidates"] = []
    assert (
        frame_diagnostic(original["point"], original["retained"])["state"]
        == "estimator_no_in_range_candidates"
    )

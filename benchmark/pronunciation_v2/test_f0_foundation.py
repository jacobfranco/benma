"""Determinism, metadata isolation, and measurement-preserving research tests."""

import dataclasses
import inspect
from pathlib import Path

import numpy as np
import pytest

from benchmark.pronunciation_v2.f0_foundation import (
    TRACKERS,
    PitchFrame,
    UtterancePitchTrack,
    basic_metrics,
    extract_utterance_pitch,
    known_f0_metrics,
    minimal_cleanup,
    sample_nearest,
    synthetic_signals,
    track_record,
    write_audio,
)


@pytest.fixture
def audio_path(tmp_path):
    t = np.arange(8000) / 16000
    audio = 0.12 * np.sin(2 * np.pi * 110 * t) + 0.05 * np.sin(2 * np.pi * 220 * t)
    path = tmp_path / "same-waveform.wav"
    write_audio(path, audio, 16000)
    return path


@pytest.mark.parametrize("tracker", TRACKERS)
def test_gibberish_metadata_cannot_change_actual_extraction(audio_path, tracker):
    """Exercise each real estimator, not a mocked or cached return value."""
    contexts = [
        {"transcript": "贵州", "target": "广州", "pinyin": "gui4 zhou1", "tone": [4, 1]},
        {"transcript": "鬼粥", "target": "nonsense", "pinyin": "invented", "tone": [1, 4]},
        {"transcript": "", "target": None, "character": None, "expected_contour": "anything"},
    ]
    results = [
        track_record({"audio_path": str(audio_path), **context}, tracker).canonical_bytes()
        for context in contexts
    ]
    assert results[0] == results[1] == results[2]


def test_contract_and_entrypoint_have_no_linguistic_fields():
    forbidden = {"character", "pinyin", "tone", "transcript", "target", "expected_contour"}
    fields = {f.name for cls in (PitchFrame, UtterancePitchTrack) for f in dataclasses.fields(cls)}
    assert not fields & forbidden
    assert set(inspect.signature(extract_utterance_pitch).parameters) == {
        "path",
        "tracker",
        "activations_path",
    }


def test_nearest_sampling_preserves_gaps_and_does_not_extrapolate():
    times = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
    values = np.array([100, 110, np.nan, np.nan, 120])
    sampled = sample_nearest(times, values, np.array([0, 0.011, 0.02, 0.031, 0.04, 0.049, 0.07]))
    np.testing.assert_equal(sampled, [np.nan, 100, 110, np.nan, np.nan, 120, np.nan])


def test_synthetic_audio_and_truth_are_byte_repeatable(tmp_path):
    a, b = synthetic_signals(tmp_path / "a"), synthetic_signals(tmp_path / "b")
    assert len(a) == len(b) == 13
    for left, right in zip(a, b, strict=True):
        assert Path(left["audio_path"]).read_bytes() == Path(right["audio_path"]).read_bytes()
        assert left.get("truth") == right.get("truth")


def test_known_truth_counts_octave_errors_and_false_gaps_separately():
    times = np.arange(0, 1, 0.01)
    truth = {"times": times.tolist(), "f0_hz": [100.0] * 100, "boundaries": []}
    measured = np.full(100, 200.0)
    measured[:20] = np.nan
    result = known_f0_metrics(times, measured, truth)
    assert result["false_gap_frames"] == 20
    assert result["octave_error_frames"] == 80
    assert result["median_error_st"] == 12
    assert result["median_absolute_hz_error"] == 100
    assert result["p95_error_st"] == result["max_error_st"] == 12
    assert result["octave_doubling_events"] == 1
    assert result["octave_doubling_frames"] == 80
    assert result["octave_halving_events"] == 0
    assert result["voiced_coverage"] == 0.8


def test_halving_and_doubling_events_do_not_merge_through_missing_evidence():
    times = np.arange(0, 0.1, 0.01)
    truth = {"times": times.tolist(), "f0_hz": [100.0] * 10, "boundaries": []}
    result = known_f0_metrics(
        times, np.array([50, 50, np.nan, 50, 100, 200, 200, np.nan, 200, 100]), truth
    )
    assert result["octave_halving_events"] == result["octave_doubling_events"] == 2
    assert result["octave_halving_frames"] == result["octave_doubling_frames"] == 3
    assert result["false_gap_frames"] == 2


def test_disjoint_review_windows_are_separate_islands():
    result = basic_metrics(np.array([0.1, 0.11, 0.5, 0.51]), np.ones(4) * 100, np.ones(4))
    assert result["islands"] == 2
    assert result["longest_run_seconds"] == pytest.approx(0.02)


def test_sparse_proxy_uses_original_cadence_instead_of_distance_between_selected_frames():
    result = basic_metrics(
        np.array([0.1, 0.7, 1.3]), np.ones(3) * 55, np.ones(3), cadence_seconds=0.01
    )
    assert result["islands"] == 3
    assert result["longest_run_seconds"] == pytest.approx(0.01)


def test_cleanup_only_removes_and_does_not_mutate_native_evidence():
    frames = tuple(PitchFrame(0.01 * i, 110.0 if i != 5 else None, 0.9, True) for i in range(10))
    track = UtterancePitchTrack("hash", "praat_ac", 16000, 0.1, 0.01, "native", {}, frames)
    before = track.canonical_bytes()
    values = minimal_cleanup(track, np.ones(1600) * 0.1)
    assert track.canonical_bytes() == before
    assert np.isnan(values[5])
    assert set(values[np.isfinite(values)]) == {110.0}

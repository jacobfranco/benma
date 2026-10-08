"""Forensic validity and explicit rejection of an unsafe run-level concept."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pytest

from benchmark.pronunciation_v2.octave_ambiguity import branches
from benchmark.pronunciation_v2.sustained_high_branch import (
    describe_path,
    nearest_candidate,
    period_evidence,
    run_features,
    screening_failures,
    spectral_evidence,
)
from benchmark.pronunciation_v2.test_octave_ambiguity import frames

REPORT = (
    Path(__file__).resolve().parents[2]
    / "docs/research/pronunciation-v2/2026-10-07-octave-ambiguity/sustained-high-evidence.json"
)


def test_replay_exact_interval_and_missing_candidates_are_not_hidden():
    data = json.loads(REPORT.read_text())
    rows = data["target"]["table"]
    assert len(rows) == 25
    assert rows[0]["timestamp_seconds"] == 4.1002
    assert rows[-1]["timestamp_seconds"] == 4.3402
    assert sum(r["production_selected_hz"] is not None for r in rows) == 24
    assert [r["timestamp_seconds"] for r in rows if r["alternate_hz"] is None] == [
        4.3002,
        4.3102,
        4.3202,
        4.3402,
    ]
    assert rows[3]["production_exclusion_reasons"] == ["weak_periodicity"]
    half = next(p for p in data["target"]["paths"] if p["ratio"] == 0.5)
    assert (half["present_frames"], half["credible_frames"]) == (16, 8)
    assert "no_after_connection" in half["screen_failures"]
    assert data["provenance"]["extraction_exact"]
    assert not data["production_changed"]


def test_direct_original_comparison_cannot_hide_downmix_or_candidate_difference():
    data = json.loads(REPORT.read_text())["original_comparison"]
    assert data["stereo_channels_sample_identical"]
    assert data["pcm_identical_after_recanonicalization"]
    assert data["waveform_correlation"] > 0.999
    assert data["max_selected_difference_st"] < 0.014
    assert data["max_strength_difference"] < 0.001
    assert data["canonical_selected_times"] == data["native_selected_times"]
    assert len(data["unmatched_candidates"]) == 1
    assert data["unmatched_candidates"][0]["canonical_candidate"]["frequency_hz"] == 49.949


def test_partial_candidate_path_has_gaps_and_all_frame_denominator():
    data = frames([360.0] * 25)
    for i, frame in enumerate(data):
        if i not in (7, 8, 19):
            frame["candidates"].append(dict(frequency_hz=180, strength=0.6))
    data[10]["selected_f0_hz"] = None
    data[10]["raw_f0_hz"] = 360
    original = copy.deepcopy(data)
    path = describe_path(data, list(range(25)), 0.5)
    assert path["coverage"] == 22 / 25
    assert path["missing_indices"] == [7, 8, 19]
    assert path["longest_credible_contiguous_frames"] == 10
    assert data == original


def test_frequency_division_is_never_used_to_invent_an_alternate():
    frame = frames([380.0])[0]
    assert nearest_candidate(frame, 0.5) is None
    frame["candidates"].append(dict(frequency_hz=210, strength=0.9))
    assert nearest_candidate(frame, 0.5) is None
    assert nearest_candidate(frame, 0.5, 2)["frequency_hz"] == 210


def test_saved_controls_preserved_but_zero_recall_is_not_acceptance():
    data = json.loads(REPORT.read_text())
    assert data["protected_summary"] == dict(samples=617, screened=0)
    assert data["protected_under70"]["samples"] == 11
    assert data["protected_under70"]["screened"] == 0
    assert len(data["controls"]) == 49
    assert all(not c["screened_indices"] for c in data["controls"])
    assert all(not c["diagnostic"]["screened_indices"] for c in data["six_physical"])
    assert all(r["before"] == r["actual_after"] for r in data["six_physical"])
    assert data["graph"]["before"] == data["graph"]["actual_after"]
    assert data["outcome"] == "D"


@pytest.mark.parametrize("direction", (-1, 1))
def test_existing_two_octave_sweep_survives_close_alternatives(direction):
    hz = [55 * 2 ** (i / 30) for i in range(61)]
    data = frames(hz if direction == 1 else hz[::-1])
    for frame in data:
        frame["candidates"].append(
            dict(frequency_hz=frame["selected_f0_hz"] * 2**-direction, strength=0.84)
        )
    assert len(branches(data)) == 1
    feature = run_features(data, list(range(61)))
    assert all(screening_failures(feature, p) for p in feature["paths"])


@pytest.mark.parametrize("hz", (54.61, 60, 70, 380))
def test_coherent_low_and_high_runs_with_stronger_octave_candidate_are_not_screened(hz):
    data = frames([hz] * 40)
    for frame in data:
        frame["candidates"].append(dict(frequency_hz=hz * (2 if hz < 100 else 0.5), strength=0.95))
    feature = run_features(data, list(range(40)))
    assert all(screening_failures(feature, p) for p in feature["paths"])


def test_candidate_only_run_screen_false_positive_on_supported_register_jump():
    # A real 220 Hz periodic signal also correlates at 1/110 s: a low candidate
    # is not evidence that 110 Hz is the fundamental. These candidate strengths
    # are an analytical counterexample, not an asserted Praat extraction.
    data = frames([110.0] * 20 + [220.0] * 25 + [110.0] * 20)
    for frame in data[20:45]:
        frame["candidates"].append(dict(frequency_hz=110, strength=0.84))
    feature = run_features(data, list(range(20, 45)))
    half = next(p for p in feature["paths"] if p["ratio"] == 0.5)
    assert not screening_failures(feature, half)  # The concept is UNSAFE without an acoustic veto.
    sr = 16000
    t = np.arange(sr) / sr
    signal = np.sin(2 * np.pi * 220 * t) + 0.3 * np.sin(2 * np.pi * 440 * t)
    evidence = period_evidence(sr, signal, 0.5, 220)
    assert evidence["hypotheses"]["high"]["correlation"] > 0.99
    assert evidence["hypotheses"]["half"]["correlation"] > 0.99
    bands = spectral_evidence(sr, signal, 0.5, 220)["0.1"]["hypothesis_bands"]
    assert bands["half"][0]["db"] < -50


def test_subharmonic_waveform_structure_distinguished_from_strongest_harmonic():
    sr = 16000
    t = np.arange(sr) / sr
    # The dominant fourth harmonic cannot turn the measured signal's period
    # into 1/(4*94). Odd harmonics and the full lag curve resolve this control.
    signal = sum(
        amplitude * np.sin(2 * np.pi * 94 * harmonic * t)
        for harmonic, amplitude in ((1, 0.2), (2, 0.4), (3, 0.5), (4, 1.0), (5, 0.3))
    )
    p = period_evidence(sr, signal, 0.5, 376)
    assert p["hypotheses"]["quarter"]["correlation"] > p["hypotheses"]["high"]["correlation"] + 0.3


def test_counterfactual_removal_preserves_ineligibility_and_metadata_independence():
    d = json.loads(REPORT.read_text())
    assert d["eligibility"][0]["production"]["state"] == "unstable"
    assert d["eligibility"][0]["deletion_only"]["state"] == "incomplete"
    assert d["eligibility"][1]["deletion_only"]["state"] == "insufficient"
    data = frames([110.0] * 20 + [220.0] * 25 + [110.0] * 20)
    before = copy.deepcopy(data)
    feature = run_features(data, list(range(20, 45)))
    for frame in data:
        frame.update(transcript="arbitrary", target="different", expected_tone=4)
    assert run_features(data, list(range(20, 45))) == feature
    for frame in data:
        for key in ("transcript", "target", "expected_tone"):
            frame.pop(key)
    assert data == before

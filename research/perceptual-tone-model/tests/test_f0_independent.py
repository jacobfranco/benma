"""Focused evidence/ownership tests; no live provider, corpus or model fitting."""

import copy
import inspect

import pytest

from perceptual_tone.common import ROOT, file_hash, read_json
from perceptual_tone.f0_independent import CANDIDATES, MIN_SECONDS, select_region
from perceptual_tone.f0_independent_replay import OUT, derive_rows


def select(*, whole=(0.1, 0.3), previous=None, following=None, energy=None,
           candidate="AZURE_WHOLE", threshold=0.1):
    return select_region(whole, previous, following, 0.5,
                         energy if energy is not None else [(i / 100, 0.2) for i in range(50)],
                         threshold, candidate)


def evidence():
    return read_json(OUT / "results.json")


def row(recording, index):
    return next(r for r in evidence()["rows"]
                if r["recording"] == recording and r["index"] == index)


@pytest.mark.parametrize("candidate", CANDIDATES)
def test_f0_failure_does_not_invalidate_safe_owned_speech(candidate):
    # Selection has no pitch inputs at all.
    result = select(candidate=candidate, previous=[0.01, 0.09], following=[0.31, 0.4])
    assert result["status"] == "valid"
    assert result["ownership_status"] == "safe"
    assert 0.095 <= result["span"][0] < result["span"][1] <= 0.3


def test_neighbor_gap_midpoint_and_touching_boundary_clamp_onset():
    candidate = "AZURE_WITH_SMALL_ONSET_CONTEXT"
    assert select(candidate=candidate, previous=[0, 0.098])["span"][0] == 0.099
    assert select(candidate=candidate, previous=[0, 0.1])["span"][0] == 0.1
    assert select(candidate=candidate, previous=[0, 0.11])["ownership_status"] == "ambiguous"
    assert select(following=[0.29, 0.4])["ownership_status"] == "ambiguous"


def test_interruption_abstains_without_selecting_largest_island():
    energy = [(i / 100, 0.01 if i == 20 else 0.2) for i in range(50)]
    result = select(energy=energy)
    assert result["reason"] == "ambiguous_interrupted_energy_support"
    assert result["span"] == [0.1, 0.3]
    assert result["internal_below_gate_centers"] == [0.2]


@pytest.mark.parametrize("threshold,energy", [
    (float("nan"), [(0.1, 0.2)]), (0.1, []), (0.1, [(0.1, float("nan"))]),
    (0.1, [(0.1, 0.2), (0.2, 0.2)]),
])
def test_missing_or_nonfinite_acoustic_evidence_fails_closed(threshold, energy):
    assert select(threshold=threshold, energy=energy)["status"] == "invalid"


def test_silence_is_not_speech_and_edge_silence_can_be_trimmed():
    assert select(energy=[(i / 100, 0.01) for i in range(50)])["reason"] == "no_energy_support"
    energy = [(i / 100, 0.2 if 15 <= i <= 25 else 0.01) for i in range(50)]
    result = select(energy=energy, candidate="AZURE_ENERGY_SUPPORTED")
    assert result["status"] == "valid"
    assert result["span"] == [0.145, 0.255]


def test_minimum_60ms_unchanged_and_sparse_support_not_enough():
    assert MIN_SECONDS == 0.06
    assert select(whole=[0.1, 0.159])["reason"] == "too_little_material"
    energy = [(0.105 + i / 100, 0.2) for i in range(6)]
    assert select(whole=[0.1, 0.16], energy=energy)["status"] == "valid"
    energy = [(i / 100, 0.2 if i in (15, 16) else 0.01) for i in range(50)]
    assert select(energy=energy)["reason"] == "too_little_material"


def test_google_frozen_case_and_separate_pitch_contract():
    r = row("google", 2)
    assert r["take_id"] == "dadff527-d15b-4ceb-a652-8bdb56c7d72d"
    assert r["pitch_evidence"]["status"] == "unavailable"
    assert r["representations"]["CURRENT_REFERENCE"]["gate_reason"] == "too_little_material"
    for name, frames in [("AZURE_WHOLE", 15), ("AZURE_ENERGY_SUPPORTED", 11)]:
        rep = r["representations"][name]
        assert rep["representation"]["status"] == "valid"
        assert rep["pooled_frames"] == frames
        assert rep["outputs"]["expanded"]["status"] == "ok"
    # No T3 assertion: Google is not tone ground truth.


def test_three_physical_takes_preserve_ownership_abstention_and_disclose_cost():
    rows = [r for r in evidence()["rows"] if r["recording"] != "google"]
    assert len(rows) == 15
    assert len({r["take_id"] for r in rows}) == 3
    for index in (1, 2):
        for name in CANDIDATES:
            rep = row("take-2", index)["representations"][name]
            assert rep["representation"]["ownership_status"] == "ambiguous"
            assert rep["pooled_frames"] == 0
            assert rep["outputs"]["expanded"]["probabilities"] is None
    assert row("take-2", 1)["representations"]["CURRENT_REFERENCE"]["pooled_frames"] > 0


def test_take3_wo_recognition_without_pitch_and_neutral_remains_outside_scope():
    r = row("take-3", 0)
    assert r["pitch_evidence"]["status"] == "unavailable"
    for name in CANDIDATES:
        assert r["representations"][name]["outputs"]["expanded"]["status"] == "ok"
    for r in evidence()["rows"]:
        if r["neutral"]:
            for rep in r["representations"].values():
                assert rep["pooled_frames"] == 0
                assert all(o["probabilities"] is None for o in rep["outputs"].values())


def test_no_text_tone_speaker_or_model_output_selection_input():
    assert list(inspect.signature(select_region).parameters) == [
        "whole", "previous", "following", "duration", "energy", "threshold", "candidate",
    ]
    raw = [{"timestamp_seconds": i / 100, "energy_rms": 0.2, "f0_hz": 100,
            "character": "买", "expected_tone": 3, "prediction": "T3"} for i in range(50)]
    mutated = copy.deepcopy(raw)
    for frame in mutated:
        frame.update(f0_hz=None, character="任意", expected_tone=1, prediction="T4")
    projected = lambda frames: [(f["timestamp_seconds"], f["energy_rms"]) for f in frames]
    assert select(energy=projected(raw)) == select(energy=projected(mutated))
    for r in evidence()["rows"]:
        for rep in r["representations"].values():
            if rep["contract"]:
                assert set(rep["contract"]) == {
                    "audio_reference", "audio_sha256", "read_unit", "pooling", "context",
                }


def test_deterministic_plan_sealed_before_inference_and_runtime_exactness():
    plan = read_json(OUT / "policy-before-inference.json")
    assert derive_rows() == plan["rows"]
    for path, sha in plan["source_hashes"].items():
        assert file_hash(ROOT / path) == sha
    results = evidence()
    assert results["policy_sha256"] == file_hash(OUT / "policy-before-inference.json")
    assert results["fresh_repeat_embedding_exact"]
    assert len(results["reference_reproduction"]) == 23
    assert all(v["max_probability_delta"] == 0 for v in results["reference_reproduction"])
    assert all(v["max_probability_delta"] < 1e-6
               for v in results["google_counterfactual_reproduction"])


def test_original_production_defaults_grading_ui_and_models_unchanged():
    before = read_json(OUT / "freeze-before.json")["files"]
    paths = [p for p in before if p.startswith(("services/api/src/", "apps/mobile/src/"))]
    assert paths
    for path in paths:
        assert file_hash(ROOT / path) == before[path]["sha256"]
    lock = read_json(ROOT / "research/perceptual-tone-model/configs/dev-learned-lock.json")
    for path, sha in lock["files"].items():
        assert file_hash(ROOT / path) == sha

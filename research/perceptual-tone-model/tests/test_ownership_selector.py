"""Frozen-case and counterexample tests; no training, corpus or inference runs."""

import copy
import inspect
import xml.etree.ElementTree as ET

import numpy as np
import pytest
from perceptual_tone import ownership_replay
from perceptual_tone.common import ROOT, file_hash, read_json
from perceptual_tone.ownership_diagnostics import OUT, audio
from perceptual_tone.ownership_replay import POLICY, acoustic_inputs, derive, verify_freeze
from perceptual_tone.ownership_selector import MIN_SECONDS, select_region


@pytest.fixture(scope="module")
def inputs():
    return {(r["recording"], r["index"]): r["inputs"] for r in acoustic_inputs()}


def choose(inp, **overrides):
    return select_region(**{**inp, **overrides}, candidate=POLICY)


@pytest.mark.parametrize("key", [("google", 2), ("take-2", 1), ("google", 3), ("take-3", 0)])
def test_positive_frozen_regions_remain_complete(inputs, key):
    result = choose(inputs[key])
    assert result["ownership"] == "safe"
    assert result["representation"] == "usable"
    assert result["span"] == inputs[key]["whole"]


def test_negative_is_two_substantial_nonfricative_islands(inputs):
    result = choose(inputs["take-2", 2])
    assert result["ownership"] == "ambiguous"
    assert result["representation"] == "abstain"
    assert result["gaps"][0]["ownership_breaking"]
    assert result["gaps"][0]["duration_ms"] == pytest.approx(40)
    assert all(r["nonfricative_ms"] >= 60 for r in result["islands"])


def test_deeper_longer_gap_can_be_fricative_onset(inputs):
    result = choose(inputs["take-2", 1])
    assert result["gaps"][0]["edge_fricative_onset"]
    assert result["gaps"][0]["duration_ms"] == pytest.approx(60)
    assert result["islands"][0]["frication_fraction"] > 0.5
    assert result["islands"][0]["nonfricative_ms"] < 60
    assert result["islands"][1]["duration_ms"] > 3 * result["islands"][0]["duration_ms"]


def test_shallow_trailing_dip_is_not_two_speech_bodies(inputs):
    result = choose(inputs["google", 3])
    gap = result["gaps"][0]
    assert not gap["deep"] and not gap["two_substantial"]
    assert gap["depression_db"] == pytest.approx(-2.476742823587073)
    assert result["islands"][-1]["duration_ms"] == pytest.approx(10)


def test_two_low_frequency_islands_cannot_use_onset_exception(inputs):
    inp = copy.deepcopy(inputs["take-2", 1])
    for row in inp["spectral"]:
        row.update(zcr=0.05, high_band_fraction=0.01)
    assert choose(inp)["ownership"] == "ambiguous"


def test_both_frication_signals_required(inputs):
    for changed in ("zcr", "high_band_fraction"):
        inp = copy.deepcopy(inputs["take-2", 1])
        for row in inp["spectral"]:
            row[changed] = 0.01
        assert choose(inp)["ownership"] == "ambiguous"


def test_generic_fricative_exception_is_not_anywhere_in_span(inputs):
    inp = copy.deepcopy(inputs["take-2", 1])
    inp["whole"][0] -= 0.030
    inp["previous"] = None
    # First island is now separated from the owner edge by acoustic silence.
    inp["energy"] = [[t, 0 if t < 1.53 else e] for t, e in inp["energy"]]
    assert choose(inp)["ownership"] == "ambiguous"


def test_neighbor_constraints_no_padding_or_overlapping_owner(inputs):
    inp = inputs["google", 2]
    assert choose(inp, previous=[1.0, 1.36], following=[1.65, 2.0])["span"] == [1.36, 1.65]
    assert choose(inp, previous=[1.0, 1.361])["ownership"] == "ambiguous"
    assert choose(inp, following=[1.649, 2.0])["ownership"] == "ambiguous"
    assert choose(inp, whole=[1.36, inp["duration"] + 0.01])["ownership"] == "invalid"


@pytest.mark.parametrize("missing", ["energy", "spectral"])
def test_missing_frames_fail_closed(inputs, missing):
    inp = copy.deepcopy(inputs["google", 2])
    key = (lambda r: r[0]) if missing == "energy" else (lambda r: r["time"])
    inp[missing] = [r for r in inp[missing] if not 1.4 < key(r) < 1.5]
    assert choose(inp)["ownership"] == "invalid"


def test_nonfinite_features_fail_closed(inputs):
    inp = copy.deepcopy(inputs["google", 2])
    inp["spectral"][0]["zcr"] = float("nan")
    assert choose(inp)["ownership"] == "invalid"


def test_minimum_stays_60ms():
    assert MIN_SECONDS == 0.060
    inp = dict(
        whole=[0.1, 0.16],
        previous=None,
        following=None,
        duration=0.5,
        energy=[[0.105 + i * 0.01, 0.2] for i in range(6)],
        threshold=0.1,
        spectral=[
            dict(time=0.1025 + i * 0.005, zcr=0.1, high_band_fraction=0.01) for i in range(12)
        ],
    )
    assert choose(inp)["representation"] == "usable"
    assert choose(inp, whole=[0.1, 0.159])["reason"] == "too_little_material"
    assert choose(inp, energy=[[t, 0] for t, _ in inp["energy"]])["representation"] == "abstain"


def test_no_pitch_identity_target_or_model_inputs():
    assert list(inspect.signature(select_region).parameters) == [
        "whole",
        "previous",
        "following",
        "duration",
        "energy",
        "threshold",
        "spectral",
        "candidate",
    ]
    source = inspect.getsource(inspect.getmodule(select_region))
    assert "load_models" not in source and "learned_runtime" not in source


def test_counterfactual_f0_and_metadata_do_not_change_any_selection(monkeypatch):
    baseline = derive()
    mutated = copy.deepcopy(ownership_replay.sources())
    for source in mutated:
        source["graph"] = None
        for frame in source["raw"]["f0"]:
            for field in list(frame):
                if field not in {"timestamp_seconds", "energy_rms"}:
                    del frame[field]
            frame.update(f0_hz=None, expected_tone=4, prediction="T1", desired_grade="red")
        for unit in source["units"]:
            unit.update(
                character="arbitrary",
                neutral=True,
                saved=None,
                saved_pool=None,
                expected_tone=1,
                speaker="arbitrary",
            )
    monkeypatch.setattr(ownership_replay, "sources", lambda: mutated)
    assert derive() == baseline


def test_determinism_and_no_input_mutation(inputs):
    before = copy.deepcopy(inputs)
    for inp in inputs.values():
        assert choose(inp) == choose(copy.deepcopy(inp))
    assert inputs == before


def test_amplitude_scaling_does_not_change_ownership(inputs):
    # Fixed existing gate scales with the same signal; relative-depth rule is invariant.
    for inp in inputs.values():
        scaled = copy.deepcopy(inp)
        scaled["energy"] = [[t, e * 0.5] for t, e in inp["energy"]]
        scaled["threshold"] *= 0.5
        assert choose(inp)["ownership"] == choose(scaled)["ownership"]


def test_saved_gate_is_exactly_reproducible_without_pitch():
    for source in ownership_replay.sources():
        values, rate = audio(source["audio"])
        width, hop = round(rate * 0.04), round(rate * 0.01)
        energy = [
            float(np.sqrt(np.mean(values[i : i + width] ** 2)))
            for i in range(0, max(1, len(values) - width + 1), hop)
        ]
        gate = max(0.003, min(3 * float(np.quantile(energy, 0.1)), max(energy) * 0.15))
        assert gate == source["raw"]["energy_gate"]["threshold_rms"]


def test_sealed_plan_and_inference_provenance():
    plan = read_json(OUT / "policy-before-inference.json")
    assert plan["rows"] == derive()
    for p, sha in {**plan["source_hashes"], **plan["diagnostic_hashes"]}.items():
        assert file_hash(ROOT / p) == sha
    evidence = read_json(OUT / "results.json")
    assert evidence["policy_sha256"] == file_hash(OUT / "policy-before-inference.json")
    assert len(evidence["rows"]) == 28
    assert evidence["encoder_cache_misses"] == 4
    for row in evidence["rows"]:
        if row["selection"]["ownership"] != "safe" or row["neutral"]:
            assert row["pooled_frames"] == 0
            assert row["outputs"]["expanded"]["probabilities"] is None


def test_full20_coverage_and_independent_pitch():
    evidence = read_json(OUT / "results.json")
    aggregate = evidence["aggregate"]
    assert aggregate["units"] == 20
    assert (aggregate["current_usable"], aggregate["new_usable"]) == (13, 15)
    assert aggregate["lost"] == []
    rows = {(r["recording"], r["index"]): r for r in evidence["rows"] if r["candidate"] == POLICY}
    for key in [("google", 2), ("take-3", 0)]:
        assert rows[key]["pitch_evidence"]["status"] == "unavailable"
        assert rows[key]["learned_representation"] == "usable"
    assert rows["take-2", 2]["pitch_evidence"]["status"] == "usable"
    assert rows["take-2", 2]["learned_representation"] == "abstain"


def test_frozen_inputs_and_previous_artifacts_unchanged():
    assert verify_freeze()["changed"] == []
    assert verify_freeze()["verified_files"] == 559


def test_aligned_plot_artifacts_are_valid_svg():
    plots = list((OUT / "diagnostics").glob("*.svg"))
    assert len(plots) == 5
    for plot in plots:
        root = ET.parse(plot).getroot()
        assert root.tag == "{http://www.w3.org/2000/svg}svg"
        assert len(root.findall("{http://www.w3.org/2000/svg}polyline")) == 7

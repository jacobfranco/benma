"""Focused offline invariants for the final candidate; no training or network."""

import copy
import inspect
import unittest

from perceptual_tone.azure_timing_replay import voiced_envelope
from perceptual_tone.common import file_hash, read_json
from perceptual_tone.fast_timing_ownership import (
    OUT, SAVED, discontinuities, ownership_alternatives, verify_freeze,
)


def synthetic(energies):
    graph = {"filtered": {"segments": [[
        {"timestamp_seconds": t, "normalized_semitones": 1.0}
        for t in [1.0, 1.01, 1.05, 1.06]
    ]]}}
    raw = {
        "energy_gate": {"threshold_rms": 0.003},
        "f0": [
            {"timestamp_seconds": t, "energy_rms": energy}
            for t, energy in zip([1.02, 1.03, 1.04], energies, strict=True)
        ],
    }
    return graph, raw


def test_pitch_dropout_is_not_silence_and_silence_is_not_reassigned():
    graph, raw = synthetic([0.1, 0.1, 0.1])
    pool = voiced_envelope(graph, [0.9, 1.1])
    assert discontinuities(graph, raw, pool) == []
    raw["f0"][1]["energy_rms"] = 0.001
    result = discontinuities(graph, raw, pool)
    assert result[0]["below_existing_energy_gate_centers"] == [1.03]
    assert voiced_envelope(graph, [0.9, 1.1]) == pool
    assert discontinuities(graph, raw, [0.9, 1.02]) == []


def test_gate_uses_existing_threshold_not_fixed_recording_specific_amplitude():
    graph, raw = synthetic([0.002, 0.004, 0.002])
    original = discontinuities(graph, raw, [0.9, 1.1])
    scaled = copy.deepcopy(raw)
    scaled["energy_gate"]["threshold_rms"] *= 7
    for frame in scaled["f0"]:
        frame["energy_rms"] *= 7
    result = discontinuities(graph, scaled, [0.9, 1.1])
    assert result[0]["below_existing_energy_gate_centers"] == original[0][
        "below_existing_energy_gate_centers"
    ]


def test_pitch_direction_text_and_model_outputs_cannot_select_spans_or_guard():
    rows = read_json(SAVED / "voiced_envelope-results.json")["rows"]
    pair = [r for r in rows if r["take"] == 2 and r["index"] in (1, 2)]
    data = read_json(SAVED / pair[0]["take_id"] / "acoustics.json")
    whole = [r["azure_whole"] for r in pair]
    alternatives = ownership_alternatives(data["graph"], data["raw"], *whole)
    pool = voiced_envelope(data["graph"], whole[1])
    issues = discontinuities(data["graph"], data["raw"], pool)
    mutated = copy.deepcopy(data)
    for container in (mutated["graph"], mutated["raw"]):
        container.update(
            character="arbitrary", expected_tone=4, learner_grade="incorrect",
            model_outputs={"prediction": "T4", "probabilities": {"T4": 1}},
        )
    for segment in mutated["graph"]["filtered"]["segments"]:
        for point in segment:
            point["normalized_semitones"] = -point["normalized_semitones"] + 100
    for point in mutated["raw"]["f0"]:
        point["f0_hz"] = 999
        point["tracker_f0_hz"] = 999
    assert ownership_alternatives(mutated["graph"], mutated["raw"], *whole) == alternatives
    assert voiced_envelope(mutated["graph"], whole[1]) == pool
    assert discontinuities(mutated["graph"], mutated["raw"], pool) == issues
    assert list(inspect.signature(discontinuities).parameters) == ["graph", "raw", "pool"]
    assert list(inspect.signature(ownership_alternatives).parameters) == [
        "graph", "raw", "left", "right"
    ]


def test_final_spans_deterministic_and_only_supported_gap_changes_gate():
    saved = read_json(SAVED / "voiced_envelope-results.json")["rows"]
    final = read_json(OUT / "final-results.json")["rows"]
    changed = []
    for old, row in zip(saved, final, strict=True):
        a, b = old["representations"]["voiced_envelope"], row["representations"]["final"]
        data = read_json(SAVED / row["take_id"] / "acoustics.json")
        assert a["contract"] == b["contract"]
        expected_pool = voiced_envelope(data["graph"], row["azure_whole"]) or row["azure_whole"]
        assert b["contract"]["pooling"] == expected_pool
        assert discontinuities(data["graph"], data["raw"], expected_pool) == b["interruptions"]
        for model in ("expanded", "pilot"):
            if a["model_outputs"][model]["status"] != b["model_outputs"][model]["status"]:
                changed.append((row["take"], row["index"], model))
                assert b["model_outputs"][model]["probabilities"] is None
                assert "embedding" not in b["model_outputs"][model]
            elif b["model_outputs"][model]["probabilities"]:
                assert a["model_outputs"][model]["probabilities"] == b["model_outputs"][model][
                    "probabilities"
                ]
    assert changed == [(2, 2, "expanded"), (2, 2, "pilot")]


def test_neutral_stays_outside_four_tone_model_and_no_support_stays_abstained():
    for row in read_json(OUT / "final-results.json")["rows"]:
        if row["outside_numbered_scope"] or (row["take"], row["index"]) == (3, 0):
            for result in row["representations"]["final"]["model_outputs"].values():
                assert result["status"] == "abstained"
                assert result["probabilities"] is None
                assert "embedding" not in result


def test_final_outputs_precede_alternative_inference_and_source_is_sealed():
    plan = read_json(OUT / "policy-before-inference.json")
    import perceptual_tone.fast_timing_ownership as module
    assert file_hash(module.__file__) == plan["source_sha256"]
    assert file_hash(SAVED / "voiced_envelope-results.json") == plan["saved_refinement_sha256"]
    result = read_json(OUT / "final-results.json")
    assert file_hash(OUT / "policy-before-inference.json") == result["policy_sha256"]
    assert (OUT / "policy-before-inference.json").stat().st_mtime_ns < (
        OUT / "final-results.json"
    ).stat().st_mtime_ns < (OUT / "alternatives.json").stat().st_mtime_ns
    assert result["performance"]["embedding_cache_hits"] == 0
    assert len(result["saved_refinement_reproduction"]) == 20
    assert all(r["max_probability_delta"] == 0 for r in result["saved_refinement_reproduction"])


def test_frozen_classifier_reference_reproduced_with_resident_encoder():
    evidence = read_json(OUT / "verification.json")
    assert evidence["resident_encoder_and_heads_reused"]
    assert len(evidence["reference_reproduction"]) == 10
    assert all(r[m] == 0 for r in evidence["reference_reproduction"] for m in ("expanded", "pilot"))


def test_every_original_file_and_production_hash_is_unchanged():
    assert verify_freeze()["verified_files"] == 2102


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(value)
        for name, value in globals().items() if name.startswith("test_")
    )

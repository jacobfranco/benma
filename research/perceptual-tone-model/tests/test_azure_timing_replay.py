"""Frozen research regressions; no training and no provider calls."""

import unittest
from unittest.mock import Mock

import numpy as np
from perceptual_tone.aishell3_learning import validate_audio_contract
from perceptual_tone.azure_timing_replay import (
    OUT,
    REFERENCE,
    audio_contract,
    geometric_frames,
    infer_region,
    verify_freeze,
    voiced_envelope,
)
from perceptual_tone.common import read_json


def graph(times):
    return {"filtered": {"segments": [
        [{"timestamp_seconds": t, "normalized_semitones": i} for i, t in enumerate(times)]
    ]}}


def test_envelope_is_generic_clamped_and_keeps_interior_gaps():
    evidence = graph([1.001, 1.011, 1.201, 1.211])
    assert np.allclose(voiced_envelope(evidence, [1, 1.213]), [1, 1.213])
    assert voiced_envelope(evidence, [1.05, 1.15]) is None
    first = voiced_envelope(evidence, [0.99, 1.3])
    for p in evidence["filtered"]["segments"][0]:
        p["normalized_semitones"] = -100
    assert voiced_envelope(evidence, [0.99, 1.3]) == first


def test_contract_rejects_every_text_or_expected_tone_channel():
    c = audio_contract("/tmp/not-read.wav", "abc", [1, 2], [1.2, 1.8], 3)
    validate_audio_contract(c)
    for field in ["text", "lexical_tone", "expected_tone", "expected_surface_tone",
                  "resolved_surface_tone", "learner_grade", "pinyin", "character"]:
        with unittest.TestCase().assertRaisesRegex(ValueError, "forbidden_encoder_input"):
            validate_audio_contract({**c, field: "forbidden"})


def test_neutral_no_support_and_short_pool_never_invoke_model():
    tid = read_json(OUT / "freeze-manifest.json")["take_order"][0]
    original = read_json(REFERENCE / "frozen" / tid / "report.json")
    audio = REFERENCE / "frozen" / tid / "canonical.wav"
    recognizer = Mock()
    c = audio_contract(audio, original["audio_sha256"], [1, 1.3], [1, 1.3], 2.7)
    neutral = infer_region(recognizer, c, graph([1.1]), outside_numbered_scope=True)
    assert neutral["model_outputs"]["expanded"]["reason"] == "neutral_outside_four_tone_model"
    no_support = infer_region(recognizer, c, graph([]))
    assert no_support["model_outputs"]["expanded"]["reason"].startswith("no_voiced_support")
    short = {**c, "pooling": [1, 1.03]}
    assert infer_region(recognizer, short, graph([1.01]))[
        "model_outputs"
    ]["expanded"]["reason"] == "too_little_material"
    recognizer.infer.assert_not_called()


def test_reference_reproduction_and_inference_contract_exactness():
    raw = read_json(OUT / "raw-results.json")
    assert len(raw["baseline_reproduction"]) == 10
    assert all(r[m] == 0 for r in raw["baseline_reproduction"] for m in ["expanded", "pilot"])
    for name in ["raw", "voiced_envelope"]:
        result = read_json(OUT / (name + "-results.json"))
        assert result["performance"]["embedding_cache_hits"] == 0
        for row in result["rows"]:
            v = row["representations"][name]
            validate_audio_contract(v["contract"])
            assert geometric_frames(v["contract"]) == v["geometric_frames"]
            for model in ("expanded", "pilot"):
                p = v["model_outputs"][model]
                if p["status"] == "ok":
                    assert p["embedding"]["owned_frames"] == v["geometric_frames"]
                    assert p["model_sha256"] == raw["rows"][0]["reference"][model]["model_sha256"]
                    assert set(p["probabilities"]) == {"T1", "T2", "T3", "T4"}
                else:
                    assert p["probabilities"] is None and p["prediction"] is None


def test_no_neutral_judgments_and_acoustic_abstention_preserved():
    for name in ["raw", "voiced_envelope"]:
        rows = read_json(OUT / (name + "-results.json"))["rows"]
        for row in rows:
            if row["outside_numbered_scope"] or (row["take"], row["index"]) == (3, 0):
                assert row["representations"][name]["model_outputs"]["expanded"]["status"] == (
                    "abstained"
                )


def test_existing_conservative_selector_did_not_create_a_distinct_representation():
    for row in read_json(OUT / "raw-results.json")["rows"]:
        a, b = [row["representations"][k] for k in ("raw", "existing_conservative")]
        assert a["contract"] == b["contract"]
        assert a["model_outputs"] == b["model_outputs"]
        assert b["reused_identical_raw_input"] and b["wall_seconds"] == 0


def test_latency_includes_provider_and_uses_measured_stages_without_cache_hits():
    latency = read_json(OUT / "latency-summary.json")
    assert latency["full_three_take_evidence_report_seconds"] > 0
    assert latency["cold_setup"]["encoder_load_seconds"] > 0
    for value in latency["takes"].values():
        fields = [
            "azure_request_seconds_including_transport_json_decode",
            "timestamp_parsing_seconds", "f0_seconds", "numeric_region_derivation_seconds",
            "warm_frozen_inference_and_gating_seconds",
        ]
        assert all(value[k] > 0 for k in fields)
        assert value["warm_sequential_core_seconds"] == sum(value[k] for k in fields)
        assert value["conservative_warm_estimate_including_entire_batch_report_seconds"] > (
            value["warm_sequential_core_seconds"]
        )


def test_all_frozen_audio_references_prior_results_models_and_production_unchanged():
    assert verify_freeze()["verified_files"] == 1999


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(value)
        for name, value in globals().items()
        if name.startswith("test_")
    )

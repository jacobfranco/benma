"""Audit sealed artifacts using cached features; never train or extract embeddings."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import joblib
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aishell3_release import verify_release
from aishell3_train import DEFAULT_RELEASE, DEFAULT_RUN, feature_matrix, probabilities
from perceptual_tone.aishell3_learning import metric
from perceptual_tone.common import PACKAGE, file_hash, read_json, read_rows
from perceptual_tone.manifest import verify_baseline


def confidence_audit(predictions):
    bins = []
    for lo, hi in zip(
        (0.25, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9), (0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0000001), strict=True
    ):
        subset = [r for r in predictions if lo <= max(r["probabilities"]) < hi]
        correct = sum(r["truth"] == r["prediction"] for r in subset)
        bins.append(
            {
                "lower": lo,
                "upper": min(hi, 1),
                "n": len(subset),
                "correct": correct,
                "incorrect": len(subset) - correct,
                "accuracy": correct / len(subset) if subset else None,
            }
        )
    if sum(b["n"] for b in bins) != len(predictions):
        raise ValueError("confidence_histogram_does_not_cover_predictions")
    return {
        "bins": bins,
        "high_confidence_errors": [
            r
            for r in predictions
            if max(r["probabilities"]) >= 0.8 and r["truth"] != r["prediction"]
        ],
    }


def audit():
    folder = DEFAULT_RUN
    baseline = verify_baseline()
    release = verify_release(DEFAULT_RELEASE)
    selected = read_json(folder / "selected.json")
    results = read_json(folder / "test-results.json")
    test_seal = read_json(folder / "test-seal.json")
    probe = read_json(folder / "external-probe.json")
    for name, sha in test_seal["files"].items():
        assert file_hash(folder / name) == sha
    external_seal = read_json(folder / "external-probe-seal.json")
    assert file_hash(folder / "external-probe.json") == external_seal["sha256"]
    assert file_hash(folder / "external-probe-protocol.json") == external_seal["protocol_sha256"]
    assert (
        selected["frozen_at"]
        < results["evaluated_at"]
        < test_seal["frozen_at"]
        < probe["protocol"]["started_at"]
    )
    protocol = read_json(folder / "protocol.json")
    for name, sha in protocol["source_hashes"].items():
        assert file_hash(PACKAGE / name) == sha
    rows = read_rows(DEFAULT_RELEASE / "primary.jsonl")
    acoustic = {r["example_id"]: r for r in read_json(folder / "acoustic-baseline.json")}
    validation = [r for r in rows if r["original"]["partition"] == "validation"]
    baseline_validation = metric(
        [r["original"]["label"] for r in validation],
        [acoustic[r["example_id"]]["prediction"] for r in validation],
    )
    test_rows = [r for r in rows if r["original"]["partition"] == "test"]
    embedded = {}
    for name in ("chinese_hubert_base", "wavlm_base_plus"):
        for view in ("target", "context"):
            file = folder / f"test-{name}-{view}.npz"
            if file.exists():
                metadata = read_json(file.with_suffix(".json"))
                assert file_hash(file) == metadata["sha256"]
                assert metadata["ids"] == [r["example_id"] for r in test_rows]
                embedded[(name, view)] = np.load(file, allow_pickle=False)["values"]
    reproduced = {}
    for family, item in selected["models"].items():
        assert file_hash(folder / item["file"]) == item["sha256"]
        model = joblib.load(folder / item["file"])
        matrix = feature_matrix(item["config"], test_rows, acoustic, embedded)
        actual = probabilities(model, matrix)
        expected = np.array([r["probabilities"] for r in results["predictions"][family]])
        np.testing.assert_allclose(actual, expected, atol=1e-12, rtol=0)
        reproduced[family] = float(np.max(np.abs(actual - expected)))
    confidence = {
        f: confidence_audit(p) for f, p in results["predictions"].items() if f != "model0_benma"
    }
    for f, a in confidence.items():
        assert len(a["high_confidence_errors"]) == results["metrics"][f]["high_confidence_errors"]
        for new, old in zip(a["bins"], results["metrics"][f]["confidence_bins"], strict=True):
            assert all(new[k] == v for k, v in old.items())
    with tempfile.TemporaryDirectory() as tmp:
        replay = Path(tmp) / "replay.jsonl"
        subprocess.run(
            [
                "node",
                str(PACKAGE / "evaluate.cjs"),
                str(PACKAGE / "stage0.dataset.jsonl"),
                str(replay),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        assert replay.read_bytes() == (PACKAGE / "stage0.baseline.jsonl").read_bytes()
    return {
        "dataset_manifest_sha256": release["manifest_sha256"],
        "baseline": baseline,
        "baseline_validation": baseline_validation,
        "baseline_validation_note": (
            "Reporting-only score from frozen outputs; baseline has no fitted/selected parameters."
        ),
        "confidence": confidence,
        "cached_test_reload_max_delta": reproduced,
        "tolerances": {
            "reload_absolute": 1e-12,
            "seeded_refit_absolute_prior_run": 1e-10,
            "fresh_embedding_absolute_prior_run": 1e-6,
            "relative": 0,
        },
        "seeded_refit_note": (
            "Previously completed exact reproduction retained; no retraining in finalization."
        ),
        "new_training_configs": 0,
        "new_encoder_extractions": 0,
        "new_training_fits": 0,
        "baseline_replay_byte_identical": True,
        "baseline_replay_examples": 63,
        "frozen_artifact_hashes": {
            name: file_hash(folder / name)
            for name in (
                "protocol.json",
                "selected.json",
                "test-results.json",
                "test-seal.json",
                "external-probe.json",
                "external-probe-seal.json",
            )
        },
    }


def check_report():
    report = (PACKAGE / "aishell3-training-report.md").read_text()
    results = read_json(DEFAULT_RUN / "test-results.json")
    for error in results["best_model_errors"]:
        assert error["example_id"] in report
        assert "/".join(f"{v:.4f}" for v in error["probabilities"]) in report
    phrase = [
        r
        for r in read_json(DEFAULT_RUN / "external-probe.json")["predictions"]
        if "我想买这个" in r["transcript"]
    ]
    for row in phrase:
        assert f"| {row['recording'][:8]} | {row['syllable']} |" in report
        assert " | ".join(f"{p:.4f}" for p in row["probabilities"]) in report
    trials = read_json(DEFAULT_RUN / "validation-trials.json")
    for t in trials:
        assert f"| {t['trial']} |" in report
        assert f"{100 * t['validation']['macro_f1']:.2f}%" in report
    assert "CORE TONE-ML FEASIBILITY: CLEARLY PROMISING" in report
    assert "CURRENT PRODUCT GENERALIZATION: MIXED / UNPROVEN" in report
    return {
        "errors_verified": len(results["best_model_errors"]),
        "phrase_syllables_verified": len(phrase),
        "validation_trials_verified": len(trials),
        "two_conclusions_present": True,
    }


if __name__ == "__main__":
    if "--check-report" in sys.argv:
        print(json.dumps(check_report(), indent=2))
    else:
        value = audit()
        (PACKAGE / "reports/aishell3-finalization-audit.json").write_text(
            json.dumps(value, indent=2) + "\n"
        )
        print(
            json.dumps(
                {k: v for k, v in value.items() if k not in ("confidence", "baseline_validation")},
                indent=2,
            )
        )

"""QA-gated fixed-method training and write-once new-speaker evaluations A and B."""

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
from threadpoolctl import threadpool_limits

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aishell3_multispeaker import verify_candidates
from aishell3_multispeaker_acquire import CONFIG, ROOT, preserve
from aishell3_release import verify_release
from aishell3_round2 import ingest_round2
from aishell3_train import DEFAULT_RUN as PILOT_RUN
from aishell3_train import acoustics, embeddings, evaluate, now
from perceptual_tone.aishell3_embeddings import LAYERS
from perceptual_tone.aishell3_generalization_analysis import analyze
from perceptual_tone.aishell3_learning import CLASSES, acoustic_vector, metric, pipeline
from perceptual_tone.aishell3_multispeaker import validate_adjudication
from perceptual_tone.common import PACKAGE, file_hash, read_json, read_rows, runtime, write_json
from perceptual_tone.manifest import verify_baseline

RUN = PACKAGE / "models/generated/aishell3-multispeaker-fixed-v2"


def checked_release(root):
    verify_candidates(root)
    config = read_json(CONFIG)
    release = root / "releases" / config["version"]
    if not (release / "release.json").exists():
        raise ValueError(
            "human_spot_check_and_immutable_release_required_before_training_or_evaluation"
        )
    info = verify_release(release)
    ingest_round2(
        root / "spot-check",
        release / "qa-export.json",
        root / "spot-check/developer-decisions.jsonl",
    )
    candidates = read_rows(root / "candidates.jsonl")
    adjudication = read_json(release / "adjudication.json")
    quarantines = validate_adjudication(
        adjudication,
        read_json(release / "qa-export.json")["reviews"],
        {r["example_id"] for r in candidates},
    )
    if read_rows(release / "manifest.jsonl") != [
        r for r in candidates if r["example_id"] not in quarantines
    ]:
        raise ValueError("release_must_equal_frozen_candidates_minus_documented_quarantines")
    return release, info


def verify_experiment_a(folder):
    result_path = folder / "experiment-A-results.json"
    seal_path = folder / "experiment-A-seal.json"
    if not result_path.exists() or not seal_path.exists():
        raise ValueError("experiment_A_must_be_frozen_before_any_experiment_B_training")
    seal = read_json(seal_path)
    for name, expected in seal["files"].items():
        if file_hash(folder / name) != expected:
            raise ValueError("frozen_experiment_A_changed:" + name)
    protocol = read_json(folder / "experiment-A-protocol.json")
    for name, expected in protocol["source_hashes"].items():
        if file_hash(PACKAGE / name) != expected:
            raise ValueError("implementation_changed_after_experiment_A:" + name)
    return read_json(result_path)


def experiment_a(root=ROOT, folder=RUN):
    release, info = checked_release(root)
    preserve(root)
    if (folder / "experiment-A-seal.json").exists():
        return verify_experiment_a(folder)
    if (folder / "models-frozen.json").exists() or list(folder.glob("*.joblib")):
        raise ValueError("experiment_A_must_precede_expanded_training")
    config = read_json(CONFIG)
    selected = read_json(PILOT_RUN / "selected.json")["models"]["model2_hubert"]
    model_path = PILOT_RUN / selected["file"]
    if file_hash(model_path) != selected["sha256"] or selected["config"] != {
        "C": 0.1,
        "encoder": "chinese_hubert_base",
        "features": "embedding",
        "kind": "logistic",
        "layer": 9,
        "view": "context",
    }:
        raise ValueError("pilot_model_identity_or_method_changed")
    folder.mkdir(parents=True, exist_ok=True)
    protocol_path = folder / "experiment-A-protocol.json"
    if not protocol_path.exists():
        write_json(
            protocol_path,
            {
                "frozen_at": now(),
                "release_sha256": file_hash(release / "release.json"),
                "manifest_sha256": info["manifest_sha256"],
                "adjudication_scope_supplement_sha256": file_hash(
                    root / "adjudication/scope-supplement.json"
                ),
                "pilot_model_sha256": selected["sha256"],
                "primary_method": config["primary"],
                "expanded_training_method_already_fixed": config["primary"],
                "runtime": runtime(),
                "retraining_before_A": False,
                "source_hashes": {
                    str(p.relative_to(PACKAGE)): file_hash(p)
                    for p in [
                        Path(__file__),
                        CONFIG,
                        PACKAGE / "perceptual_tone/aishell3_generalization_analysis.py",
                        PACKAGE / "perceptual_tone/aishell3_learning.py",
                        PACKAGE / "perceptual_tone/aishell3_embeddings.py",
                        PACKAGE / "scripts/aishell3_train.py",
                        PACKAGE / "configs/encoders.json",
                    ]
                },
            },
        )
    protocol = read_json(protocol_path)
    if protocol["release_sha256"] != file_hash(release / "release.json"):
        raise ValueError("release_changed_after_A_opened")
    for name, expected in protocol["source_hashes"].items():
        if file_hash(PACKAGE / name) != expected:
            raise ValueError("A_implementation_changed")
    test = [r for r in read_rows(release / "primary.jsonl") if r["original"]["partition"] == "test"]
    values = embeddings(test, "chinese_hubert_base", "context", folder, "test")[
        :, LAYERS.index(9), :
    ]
    predictions_path = folder / "experiment-A-predictions.json"
    if predictions_path.exists():
        raise ValueError(
            "unsealed_A_predictions_exist_requires_integrity_recovery_not_reprediction"
        )
    model = joblib.load(model_path)
    if model.n_features_in_ != 768:
        raise ValueError("pilot_feature_dimension_mismatch")
    with threadpool_limits(limits=4):
        _, probabilities = evaluate(model, values, [r["original"]["label"] for r in test])
    write_json(
        predictions_path,
        {
            "ids": [r["example_id"] for r in test],
            "probabilities": probabilities.tolist(),
            "pilot_model_sha256": file_hash(model_path),
            "evaluated_at": now(),
        },
    )
    pred = np.asarray(CLASSES)[probabilities.argmax(1)]
    result = {
        "status": "FROZEN_OLD_MODEL_NEW_SPEAKERS_NO_RETRAINING",
        "evaluated_at": now(),
        "release_manifest_sha256": info["manifest_sha256"],
        "test_speakers": read_json(release / "split.json")["partitions"]["test"]["speakers"],
        "analysis": analyze(
            test, pred, probabilities, read_json(release / "prosody.json")["exact_matches"]
        ),
    }
    write_json(folder / "experiment-A-results.json", result)
    write_json(
        folder / "experiment-A-seal.json",
        {
            "sealed_at": now(),
            "files": {
                p.name: file_hash(p)
                for p in (protocol_path, predictions_path, folder / "experiment-A-results.json")
            },
        },
    )
    return verify_experiment_a(folder)


def run(root=ROOT, folder=RUN):
    release, info = checked_release(root)  # Must precede extraction, fits and predictions.
    experiment_a_result = verify_experiment_a(folder)
    preserve(root)
    config = read_json(CONFIG)
    expected = {
        "encoder": "chinese_hubert_base",
        "revision": "fce0375452b1dd6c080ac3248d423d4d037bc831",
        "frozen": True,
        "view": "context",
        "layer": 9,
        "pooling": "tone_bearing_frame_center_mean",
        "classifier": "logistic_regression",
        "class_weight": "balanced",
        "C": 0.1,
    }
    if config["primary"] != expected:
        raise ValueError("frozen_primary_method_changed")
    selected = read_json(PILOT_RUN / "selected.json")["models"]["model2_hubert"]
    if selected["config"] != {
        "C": 0.1,
        "encoder": "chinese_hubert_base",
        "features": "embedding",
        "kind": "logistic",
        "layer": 9,
        "view": "context",
    }:
        raise ValueError("pilot_representation_incompatible")
    old_path = PILOT_RUN / selected["file"]
    if file_hash(old_path) != selected["sha256"]:
        raise ValueError("old_model_changed")
    folder.mkdir(parents=True, exist_ok=True)
    protocol_path = folder / "protocol.json"
    if not protocol_path.exists():
        write_json(
            protocol_path,
            {
                "created": now(),
                "method": expected,
                "release_sha256": file_hash(release / "release.json"),
                "manifest_sha256": info["manifest_sha256"],
                "split_sha256": file_hash(release / "split.json"),
                "experiment_A_seal_sha256": file_hash(folder / "experiment-A-seal.json"),
                "config_sha256": file_hash(CONFIG),
                "pilot_model_sha256": selected["sha256"],
                "baseline": verify_baseline(),
                "runtime": runtime(),
                "validation": "sanity report only; zero configuration search",
                "secondary_acoustic_C": 1.0,
                "wavlm": (
                    "omitted to avoid a second full encoder extraction; "
                    "prior context/layer6/C0.1 remains frozen"
                ),
                "external_probe": "omitted; corpus generalization only",
                "source_hashes": {
                    str(p.relative_to(PACKAGE)): file_hash(p)
                    for p in [
                        Path(__file__),
                        PACKAGE / "perceptual_tone/aishell3_generalization_analysis.py",
                        PACKAGE / "perceptual_tone/aishell3_learning.py",
                        PACKAGE / "perceptual_tone/aishell3_embeddings.py",
                        PACKAGE / "scripts/aishell3_train.py",
                        PACKAGE / "configs/encoders.json",
                    ]
                },
            },
        )
    protocol = read_json(protocol_path)
    if (
        protocol["release_sha256"] != file_hash(release / "release.json")
        or protocol["config_sha256"] != file_hash(CONFIG)
        or protocol["pilot_model_sha256"] != file_hash(old_path)
    ):
        raise ValueError("frozen_protocol_changed")
    for name, expected_hash in protocol["source_hashes"].items():
        if file_hash(PACKAGE / name) != expected_hash:
            raise ValueError("frozen_research_implementation_changed:" + name)
    result_path = folder / "test-results.json"
    if result_path.exists():
        if file_hash(result_path) != read_json(folder / "test-seal.json")["sha256"]:
            raise ValueError("sealed_test_results_changed")
        return read_json(result_path)
    rows = read_rows(release / "primary.jsonl")
    tv = [r for r in rows if r["original"]["partition"] != "test"]
    train_mask = np.asarray([r["original"]["partition"] == "train" for r in tv])
    labels = np.asarray([r["original"]["label"] for r in tv])
    freeze_path = folder / "models-frozen.json"
    if not freeze_path.exists():
        vectors = embeddings(tv, "chinese_hubert_base", "context", folder, "train-validation")[
            :, LAYERS.index(9), :
        ]
        acoustic = {
            r["example_id"]: r for r in acoustics(tv, folder / "train-validation-acoustics")
        }
        acoustic_values = np.stack([acoustic_vector(acoustic[r["example_id"]])[1] for r in tv])
        fitted = {}
        for name, values, C in (
            ("experiment_B", vectors, 0.1),
            ("acoustic_LR", acoustic_values, 1.0),
        ):
            with threadpool_limits(limits=4):
                model = pipeline("logistic", C).fit(values[train_mask], labels[train_mask])
                reference = pipeline("logistic", C).fit(values[train_mask], labels[train_mask])
                np.testing.assert_allclose(
                    model.predict_proba(values), reference.predict_proba(values), atol=1e-10, rtol=0
                )
                validation, prob = evaluate(model, values[~train_mask], labels[~train_mask])
            destination = folder / (name + ".joblib")
            if destination.exists():
                raise ValueError("unsealed_model_exists_recovery_requires_audit")
            joblib.dump(model, destination)
            np.testing.assert_allclose(
                joblib.load(destination).predict_proba(values[~train_mask]),
                prob,
                atol=1e-12,
                rtol=0,
            )
            fitted[name] = {
                "file": destination.name,
                "sha256": file_hash(destination),
                "C": C,
                "feature_dimensions": values.shape[1],
                "validation": validation,
                "reload_passed": True,
                "seeded_refit_passed": True,
            }
        write_json(
            freeze_path,
            {"frozen_at": now(), "protocol_sha256": file_hash(protocol_path), "models": fitted},
        )
    frozen = read_json(freeze_path)
    if frozen["protocol_sha256"] != file_hash(protocol_path):
        raise ValueError("model_protocol_changed")
    for m in frozen["models"].values():
        if file_hash(folder / m["file"]) != m["sha256"]:
            raise ValueError("frozen_model_changed")
    # A is already sealed. B opens its test evaluation only after its own heads freeze.
    if not (folder / "test-opened.json").exists():
        write_json(
            folder / "test-opened.json",
            {
                "opened_at": now(),
                "models_sha256": file_hash(freeze_path),
                "policy": (
                    "one prediction pass per model; persisted predictions reused for reporting"
                ),
            },
        )
    if read_json(folder / "test-opened.json")["models_sha256"] != file_hash(freeze_path):
        raise ValueError("test_opened_with_different_models")
    test = [r for r in rows if r["original"]["partition"] == "test"]
    truth = [r["original"]["label"] for r in test]
    vectors = embeddings(test, "chinese_hubert_base", "context", folder, "test")[
        :, LAYERS.index(9), :
    ]
    acoustic = {r["example_id"]: r for r in acoustics(test, folder / "test-acoustics")}
    acoustic_values = np.stack([acoustic_vector(acoustic[r["example_id"]])[1] for r in test])
    prosody = read_json(release / "prosody.json")["exact_matches"]
    baseline_predictions = [acoustic[r["example_id"]]["prediction"] for r in test]
    results = {
        "deterministic_Benma": analyze(test, baseline_predictions, prosody=prosody),
        "experiment_A": experiment_a_result["analysis"],
    }
    for name, path, values in (
        ("experiment_B", folder / frozen["models"]["experiment_B"]["file"], vectors),
        ("acoustic_LR", folder / frozen["models"]["acoustic_LR"]["file"], acoustic_values),
    ):
        pred_path = folder / (name + "-test-predictions.json")
        if pred_path.exists():
            if file_hash(pred_path) != read_json(pred_path.with_suffix(".seal.json"))["sha256"]:
                raise ValueError("predictions_changed")
            saved = read_json(pred_path)
            if saved["ids"] != [r["example_id"] for r in test] or saved[
                "model_sha256"
            ] != file_hash(path):
                raise ValueError("prediction_identity_changed")
            probs = np.asarray(saved["probabilities"])
        else:
            model = joblib.load(path)
            with threadpool_limits(limits=4):
                _, probs = evaluate(model, values, truth)
            write_json(
                pred_path,
                {
                    "ids": [r["example_id"] for r in test],
                    "model_sha256": file_hash(path),
                    "probabilities": probs.tolist(),
                    "evaluated_at": now(),
                },
            )
            write_json(pred_path.with_suffix(".seal.json"), {"sha256": file_hash(pred_path)})
        pred = np.asarray(CLASSES)[probs.argmax(1)]
        results[name] = analyze(
            test,
            pred,
            probs,
            prosody,
            bootstrap_replicates=2000 if name.startswith("experiment") else 0,
        )
        covered = np.asarray([p is not None for p in baseline_predictions])
        results[name]["same_examples_as_covered_Benma"] = metric(
            np.asarray(truth)[covered], pred[covered], probs[covered]
        )
    final = {
        "status": "EVALUATED_FIXED_METHOD_NO_RETUNING",
        "evaluated_at": now(),
        "release_manifest_sha256": info["manifest_sha256"],
        "models_sha256": file_hash(freeze_path),
        "split": read_json(release / "split.json"),
        "validation": frozen["models"],
        "results": results,
        "external_probe": "not_run",
        "wavlm": protocol["wavlm"],
    }
    write_json(result_path, final)
    write_json(folder / "test-seal.json", {"sha256": file_hash(result_path), "sealed_at": now()})
    preserve(root)
    return final


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["experiment-a", "experiment-b", "verify-a"])
    args = parser.parse_args()
    result = {
        "experiment-a": experiment_a,
        "experiment-b": run,
        "verify-a": lambda: verify_experiment_a(RUN),
    }[args.action]()
    print(
        json.dumps(
            {
                "status": result["status"],
                "metrics": result.get("analysis", {}).get("overall"),
                "per_speaker": {
                    s: {"n": m["n"], "accuracy": m["accuracy"]}
                    for s, m in result.get("analysis", {}).get("per_speaker", {}).items()
                },
                "test_results_directory": str(RUN),
            },
            indent=2,
        )
    )

"""Bounded frozen probe with separate selection, locked test, and secondary stages."""

import argparse
import collections
import csv
import importlib.metadata
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from features import LAYERS, MODEL_ID, PREPROCESSING, extract
from preflight import sha256, write_csv, write_json
from remediate import GROUPS, validate_split
from scipy.special import softmax
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

SEED = 20260929
CS = (0.1, 1.0, 10.0)
OUTPUT = Path("docs/research/pronunciation-v2/2026-09-29-frozen-wav2vec")
CACHE = Path.home() / ".cache/benma/pronunciation-v2-model"
CORPUS = Path("docs/research/pronunciation-v2/2026-09-28-data-feasibility/pilot-manifest.jsonl")
CODE = Path(__file__).resolve().parent


def now():
    return datetime.now(UTC).isoformat()


def versions():
    return {
        p: importlib.metadata.version(p)
        for p in ("torch", "transformers", "scikit-learn", "numpy", "scipy", "huggingface-hub")
    }


def rows_at(output):
    rows = list(csv.DictReader((output / "split-manifest.csv").open()))
    validate_split(rows)
    return rows


def exclusive_json(path, value):
    with path.open("x") as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def metrics(y, prediction):
    precision, recall, f1, support = precision_recall_fscore_support(
        y,
        prediction,
        labels=[1, 2, 3, 4],
        zero_division=0,
    )
    return {
        "n": len(y),
        "accuracy": float(accuracy_score(y, prediction)),
        "balanced_accuracy": float(np.mean(recall)),
        "macro_f1": float(np.mean(f1)),
        "per_tone": {
            str(t): {
                "precision": float(precision[t - 1]),
                "recall": float(recall[t - 1]),
                "f1": float(f1[t - 1]),
                "support": int(support[t - 1]),
            }
            for t in range(1, 5)
        },
        "confusion_matrix": confusion_matrix(y, prediction, labels=[1, 2, 3, 4]).tolist(),
    }


def fit_head(x, y):
    # Caller supplies train rows only. Validation/test arrays never enter fit.
    scaler = StandardScaler().fit(x)
    return scaler, scaler.transform(x)


def fit_classifier(x, y, c):
    with threadpool_limits(limits=1):
        model = LogisticRegression(
            C=c,
            solver="lbfgs",
            penalty="l2",
            class_weight=None,
            max_iter=3000,
            tol=1e-8,
            random_state=SEED,
        ).fit(x, y)
    if model.n_iter_.max() >= 3000:
        raise RuntimeError("Linear optimizer did not converge")
    if not np.array_equal(model.classes_, [1, 2, 3, 4]):
        raise ValueError("All four classes required")
    return model


def selection_key(candidate):
    # Effectively tied = equality at 12 decimals, then fixed lower-layer last tie break.
    return (
        round(candidate["macro_f1"], 12),
        round(candidate["balanced_accuracy"], 12),
        round(candidate["t2_t3_mean_recall"], 12),
        -candidate["C"],
        -candidate["layer"],
    )


def download(cache, output):
    from huggingface_hub import HfApi, hf_hub_download

    info = HfApi().model_info(MODEL_ID)
    revision = info.sha
    if info.card_data.get("license") != "apache-2.0":
        raise ValueError("Checkpoint license differs from prior reconnaissance")
    files = {f.rfilename for f in info.siblings}
    weight = "model.safetensors" if "model.safetensors" in files else "pytorch_model.bin"
    paths = {}
    for name in ("config.json", "preprocessor_config.json", "README.md", weight):
        paths[name] = hf_hub_download(MODEL_ID, name, revision=revision, cache_dir=cache / "hf")
    record = {
        "model_id": MODEL_ID,
        "revision": revision,
        "license": "apache-2.0",
        "snapshot": str(Path(paths["config.json"]).parent),
        "downloaded_at": now(),
        "files_sha256": {name: sha256(Path(path)) for name, path in paths.items()},
    }
    write_json(output / "checkpoint.json", record)
    print(json.dumps(record, indent=2))


def code_hashes():
    return {
        name: sha256(CODE / name)
        for name in ("features.py", "model_probe.py", "remediate.py", "v1_adapter.py")
    }


def select(output, cache):
    if (output / "experiment-config.locked.json").exists():
        raise FileExistsError("Selection already locked")
    rows = rows_at(output)
    development = [r for r in rows if r["partition"] in ("train", "validation")]
    checkpoint = json.loads((output / "checkpoint.json").read_text())
    path = cache / "development-features.npz"
    extraction = extract(development, checkpoint["snapshot"], path)
    write_json(output / "development-extraction.json", extraction)
    features = np.load(path, allow_pickle=False)
    y = np.array([int(r["tone"]) for r in development])
    train = np.array([r["partition"] == "train" for r in development])
    candidates, heads = [], {}
    for layer in LAYERS:
        x = features[f"layer_{layer}"]
        scaler, train_x = fit_head(x[train], y[train])
        for c in CS:
            model = fit_classifier(train_x, y[train], c)
            prediction = model.predict(scaler.transform(x[~train]))
            result = metrics(y[~train], prediction)
            candidate = {
                "layer": layer,
                "C": c,
                "n": result["n"],
                **{k: result[k] for k in ("accuracy", "balanced_accuracy", "macro_f1")},
                "t2_t3_mean_recall": np.mean(
                    [result["per_tone"][str(t)]["recall"] for t in (2, 3)]
                ),
                "iterations": int(model.n_iter_.max()),
            }
            candidates.append(candidate)
            heads[layer, c] = scaler, model
    write_csv(output / "validation-results.csv", candidates)
    winner = max(candidates, key=selection_key)
    scaler, model = heads[winner["layer"], winner["C"]]
    head = cache / "selected-head.npz"
    np.savez_compressed(
        head,
        mean=scaler.mean_,
        scale=scaler.scale_,
        var=scaler.var_,
        coef=model.coef_,
        intercept=model.intercept_,
        classes=model.classes_,
    )
    x = features[f"layer_{winner['layer']}"][~train]
    assert np.allclose(predict_head(head, x), model.predict_proba(scaler.transform(x)), atol=1e-12)
    locked = {
        "locked_at": now(),
        "seed": SEED,
        "selected_layer": winner["layer"],
        "selected_C": winner["C"],
        "grid": {"layers": list(LAYERS), "C": list(CS)},
        "selection": (
            "validation macro F1; balanced accuracy; mean T2/T3 recall; "
            "smaller C; lower layer; round metrics to 12 decimals"
        ),
        "preprocessing": PREPROCESSING,
        "model": checkpoint,
        "versions": versions(),
        "head": "multinomial logistic regression; L2; lbfgs; unweighted; max_iter=3000; tol=1e-8",
        "normalization": (
            "StandardScaler fitted on training clips only; per feature population variance"
        ),
        "hidden_layer_indexing": (
            "hidden_states[0] pre-transformer; hidden_states[k] output after transformer block k"
        ),
        "split_manifest_sha256": sha256(output / "split-manifest.csv"),
        "clean_manifest_sha256": sha256(output / "clean-corpus-manifest.csv"),
        "corpus_manifest_sha256": sha256(CORPUS),
        "validation_results_sha256": sha256(output / "validation-results.csv"),
        "head_sha256": sha256(head),
        "development_features_sha256": sha256(path),
        "research_code_sha256": code_hashes(),
        "train_tones": dict(collections.Counter(str(t) for t in y[train])),
        "hidden_size": extraction["hidden_size"],
        "device": extraction["device"],
        "test_opened": False,
        "no_expected_tone_text_pinyin_f0_asr_speaker_inputs": True,
    }
    exclusive_json(output / "experiment-config.locked.json", locked)
    print(
        json.dumps(
            {"winner": winner, "locked_sha256": sha256(output / "experiment-config.locked.json")},
            indent=2,
        )
    )


def require_lock(output, cache):
    lock_path = output / "experiment-config.locked.json"
    locked = json.loads(lock_path.read_text())
    for file, key in (
        ("split-manifest.csv", "split_manifest_sha256"),
        ("clean-corpus-manifest.csv", "clean_manifest_sha256"),
        ("validation-results.csv", "validation_results_sha256"),
    ):
        if sha256(output / file) != locked[key]:
            raise ValueError("Changed locked artifact: " + file)
    if (
        sha256(CORPUS) != locked["corpus_manifest_sha256"]
        or sha256(cache / "selected-head.npz") != locked["head_sha256"]
        or sha256(cache / "development-features.npz") != locked["development_features_sha256"]
        or code_hashes() != locked["research_code_sha256"]
        or versions() != locked["versions"]
    ):
        raise ValueError("Locked inputs, code, environment or model changed")
    for name, digest in locked["model"]["files_sha256"].items():
        if sha256(Path(locked["model"]["snapshot"]) / name) != digest:
            raise ValueError("Checkpoint changed")
    return locked


def predict_head(path, x):
    head = np.load(path, allow_pickle=False)
    if not np.array_equal(head["classes"], [1, 2, 3, 4]):
        raise ValueError("Unexpected class order")
    return softmax(
        ((x - head["mean"]) / head["scale"]) @ head["coef"].T + head["intercept"], axis=1
    )


def prediction_rows(rows, probability):
    result = []
    for row, p in zip(rows, probability, strict=True):
        ordered = np.sort(p)
        result.append(
            {
                **{
                    key: row[key]
                    for key in (
                        "source_asset_id",
                        "text",
                        "pinyin",
                        "tone",
                        "speaker_id",
                        "duration_seconds",
                        "rms",
                        "peak_level",
                        "silence_ratio",
                        "clipping_percentage",
                    )
                },
                "prediction": int(np.argmax(p)) + 1,
                **{f"p_T{t}": float(p[t - 1]) for t in range(1, 5)},
                "max_softmax": float(p.max()),
                "entropy_nats": float(-np.sum(p * np.log(np.maximum(p, 1e-300)))),
                "top1_top2_margin": float(ordered[-1] - ordered[-2]),
            }
        )
    return result


def test(output, cache):
    locked = require_lock(output, cache)
    receipt = output / "primary-test-opened.json"
    exclusive_json(
        receipt,
        {
            "opened_at": now(),
            "locked_config_sha256": sha256(output / "experiment-config.locked.json"),
            "policy": "one primary test invocation; no silent retry or post-test model change",
        },
    )
    rows = [r for r in rows_at(output) if r["partition"] == "test"]
    path = cache / "test-features.npz"
    extraction = extract(
        rows, locked["model"]["snapshot"], path, layers=(locked["selected_layer"],)
    )
    write_json(output / "test-extraction.json", extraction)
    probability = predict_head(
        cache / "selected-head.npz", np.load(path)[f"layer_{locked['selected_layer']}"]
    )
    records = prediction_rows(rows, probability)
    write_csv(output / "test-results.csv", records)
    y = [int(r["tone"]) for r in rows]
    result = metrics(y, [r["prediction"] for r in records])
    majority = int(max(locked["train_tones"], key=locked["train_tones"].get))
    report = {
        "primary": result,
        "majority_class": majority,
        "majority": metrics(y, [majority] * len(y)),
        "uniform_chance_expected_accuracy": 0.25,
        "recorded_at": now(),
        "locked_config_sha256": sha256(output / "experiment-config.locked.json"),
        "test_results_sha256": sha256(output / "test-results.csv"),
        "softmax_calibrated": False,
    }
    exclusive_json(output / "primary-metrics.json", report)
    print(json.dumps(report, indent=2))


def groups(output, cache):
    locked = require_lock(output, cache)
    primary = json.loads((output / "primary-metrics.json").read_text())
    if primary["test_results_sha256"] != sha256(output / "test-results.csv"):
        raise ValueError("Primary result changed")
    rows = rows_at(output)
    lookup = {}
    for path in (cache / "development-features.npz", cache / "test-features.npz"):
        features = np.load(path)
        lookup.update(
            zip(features["asset_ids"], features[f"layer_{locked['selected_layer']}"], strict=True)
        )
    x = np.stack([lookup[r["source_asset_id"]] for r in rows])
    y = np.array([int(r["tone"]) for r in rows])
    summaries, predictions, detailed = [], [], {}
    for group in GROUPS:
        held = np.array([r["speaker_id"] == group for r in rows])
        scaler, train_x = fit_head(x[~held], y[~held])
        model = fit_classifier(train_x, y[~held], locked["selected_C"])
        p = model.predict_proba(scaler.transform(x[held]))
        result = metrics(y[held], np.argmax(p, axis=1) + 1)
        detailed[group] = result
        summaries.append(
            {
                "group": group,
                **{k: result[k] for k in ("n", "accuracy", "balanced_accuracy", "macro_f1")},
                **{f"recall_T{t}": result["per_tone"][str(t)]["recall"] for t in range(1, 5)},
                "confusion_matrix": json.dumps(result["confusion_matrix"]),
            }
        )
        predictions.extend(prediction_rows([r for r, h in zip(rows, held, strict=True) if h], p))
    write_csv(output / "source-group-evaluation.csv", summaries)
    write_csv(output / "source-group-predictions.csv", predictions)
    aggregate = metrics(
        [int(r["tone"]) for r in predictions], [r["prediction"] for r in predictions]
    )
    write_json(
        output / "source-group-metrics.json",
        {
            "per_group": detailed,
            "aggregate_oof": aggregate,
            "mean_group_macro_f1": float(np.mean([r["macro_f1"] for r in summaries])),
            "scope": (
                "secondary fixed-config source-group held-out diagnostic; not a pristine new test"
            ),
        },
    )
    print(json.dumps({"groups": summaries, "aggregate": aggregate}, indent=2))


def compare(output, cache):
    require_lock(output, cache)
    subprocess.run(
        [
            "services/api/.venv/bin/python",
            str(CODE / "v1_adapter.py"),
            "--output",
            str(output),
            "--cache",
            str(cache),
        ],
        check=True,
    )
    v2 = list(csv.DictReader((output / "test-results.csv").open()))
    v1 = {r["source_asset_id"]: r for r in list(csv.DictReader((output / "v1-results.csv").open()))}
    combined = [
        {**r, **{k: v for k, v in v1[r["source_asset_id"]].items() if k != "source_asset_id"}}
        for r in v2
    ]
    covered = [r for r in combined if r["v1_category"] in ("1", "2", "3", "4")]
    y = [int(r["tone"]) for r in covered]
    report = {
        "total_n": len(v2),
        "covered_n": len(covered),
        "coverage": len(covered) / len(v2),
        "abstention_count": len(v2) - len(covered),
        "per_tone_coverage": {
            str(t): sum(int(r["tone"]) == t for r in covered)
            / sum(int(r["tone"]) == t for r in combined)
            for t in range(1, 5)
        },
        "v1_covered": metrics(y, [int(r["v1_category"]) for r in covered]) if covered else None,
        "v2_common_subset": metrics(y, [int(r["prediction"]) for r in covered])
        if covered
        else None,
    }
    write_csv(output / "v1-comparison.csv", combined)
    errors = []
    train = [r for r in rows_at(output) if r["partition"] == "train"]
    for row in combined:
        if row["tone"] != row["prediction"]:
            errors.append(
                {
                    **row,
                    "t2_t3_confusion": {row["tone"], row["prediction"]} == {"2", "3"},
                    "high_max_softmax_diagnostic_only": float(row["max_softmax"]) >= 0.9,
                    "text_seen_in_train": any(r["text"] == row["text"] for r in train),
                    "pinyin_seen_in_train": any(r["pinyin"] == row["pinyin"] for r in train),
                }
            )
    if errors:
        write_csv(output / "error-analysis.csv", errors)
    result = json.loads((output / "primary-metrics.json").read_text())
    result["v1_comparison"] = report
    result["source_group_diagnostic"] = json.loads(
        (output / "source-group-metrics.json").read_text()
    )
    write_json(output / "metrics.json", result)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["download", "select", "test", "groups", "compare"])
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--cache", type=Path, default=CACHE)
    args = parser.parse_args()
    globals()[args.stage](args.cache, args.output) if args.stage == "download" else globals()[
        args.stage
    ](args.output, args.cache)

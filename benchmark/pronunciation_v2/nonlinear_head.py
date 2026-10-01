"""Experiment 3 fixed head: preflight, reproduction and training only; no test CLI."""

import argparse
import json
import random
from pathlib import Path
from types import MappingProxyType

import numpy as np
import torch
from features import PREPROCESSING, extract
from model_probe import exclusive_json, now, predict_head
from preflight import sha256
from sklearn.preprocessing import StandardScaler
from temporal_pooling import (
    CLASSIFIER,
    OLD,
    OLD_CACHE,
    REVISION,
    ROOT,
    SCALER,
    SPLIT_HASH,
    arrays_hash,
    csv_rows,
    environment,
    fit_fixed,
    save_arrays,
    summarize,
)

CODE = Path(__file__).resolve().parent
OUT = ROOT / "docs/research/pronunciation-v2/2026-10-01-experiment-3-preflight"
CACHE = ROOT / "benchmark/corpus/recordings/original/experiment-3-cache"
CONFIG = MappingProxyType(
    dict(
        input_width=768,
        hidden_width=8,
        output_width=4,
        activation="tanh",
        parameter_count=6188,
        seed=20261001,
        initialization="Xavier uniform gain=1 for both weights; zero biases",
        optimizer="AdamW",
        learning_rate=0.001,
        betas=[0.9, 0.999],
        eps=1e-8,
        weight_decay=0.01,
        decay_parameters="both weight matrices only; biases have zero decay",
        batch_size=386,
        epochs=200,
        stopping="exactly 200 updates; final epoch; nonfinite loss/gradients abort",
        loss="unweighted mean cross entropy; class indices T1=0 through T4=3",
        shuffle=False,
        dropout=0.0,
        device="cpu",
        dtype="float32",
        torch_threads=1,
        deterministic_algorithms=True,
        seed_policy="one seed; no best-seed selection or ensemble",
    )
)


def configure():
    random.seed(CONFIG["seed"])
    np.random.seed(CONFIG["seed"])
    torch.manual_seed(CONFIG["seed"])
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)


def make_head():
    configure()
    head = torch.nn.Sequential(torch.nn.Linear(768, 8), torch.nn.Tanh(), torch.nn.Linear(8, 4)).to(
        device="cpu", dtype=torch.float32
    )
    for layer in (head[0], head[2]):
        torch.nn.init.xavier_uniform_(layer.weight, gain=1.0)
        torch.nn.init.zeros_(layer.bias)
    return head


def fit_standardized(x, y):
    """Fixed algorithm; synthetic tests use this core without real-data membership gates."""
    x = np.asarray(x)
    y = np.asarray(y)
    if x.ndim != 2 or x.shape[1] != 768 or len(x) != len(y) or not len(x):
        raise ValueError("Expected aligned N x 768 features")
    if not np.isfinite(x).all() or y.dtype.kind not in "iu" or set(y) != {1, 2, 3, 4}:
        raise ValueError("Finite features and integer T1-T4 labels required")
    head = make_head()
    optimizer = torch.optim.AdamW(
        [
            {"params": [head[0].weight, head[2].weight], "weight_decay": 0.01},
            {"params": [head[0].bias, head[2].bias], "weight_decay": 0.0},
        ],
        lr=0.001,
        betas=(0.9, 0.999),
        eps=1e-8,
        amsgrad=False,
        foreach=False,
        fused=False,
    )
    inputs = torch.tensor(x, dtype=torch.float32, device="cpu")
    targets = torch.tensor(y - 1, dtype=torch.long, device="cpu")
    losses = []
    head.train()
    for _ in range(CONFIG["epochs"]):
        optimizer.zero_grad(set_to_none=True)
        loss = torch.nn.functional.cross_entropy(head(inputs), targets, reduction="mean")
        if not torch.isfinite(loss):
            raise RuntimeError("Nonfinite loss; abort without changing protocol")
        loss.backward()
        if any(not torch.isfinite(p.grad).all() for p in head.parameters()):
            raise RuntimeError("Nonfinite gradient; abort without changing protocol")
        optimizer.step()
        if any(not torch.isfinite(p).all() for p in head.parameters()):
            raise RuntimeError("Nonfinite parameters; abort without changing protocol")
        losses.append(float(loss.detach()))
    head.eval()
    return head, losses


def authoritative_rows():
    path = OLD / "split-manifest.csv"
    if sha256(path) != SPLIT_HASH:
        raise ValueError("Frozen split changed")
    return csv_rows(path)


def validate_training(rows):
    expected = [r for r in authoritative_rows() if r["partition"] == "train"]
    # Full row equality protects labels, provenance, order, identities and membership.
    if len(rows) != 386 or rows != expected:
        raise ValueError("Only the exact ordered original 386 training rows are permitted")
    if any(r["tone"] not in {"1", "2", "3", "4"} for r in rows):
        raise ValueError("Only T1-T4")


def fit_nonlinear(x, rows):
    validate_training(rows)
    if x.shape != (386, 768):
        raise ValueError("Expected frozen layer-8 whole-mean features")
    scaler = StandardScaler(**SCALER).fit(x)
    head, losses = fit_standardized(scaler.transform(x), np.array([int(r["tone"]) for r in rows]))
    arrays = {k: v.detach().numpy() for k, v in head.state_dict().items()}
    arrays.update(mean=scaler.mean_, scale=scaler.scale_, var=scaler.var_)
    return arrays, losses


def comparison(rows, linear_prediction, nonlinear_prediction):
    if not (len(rows) == len(linear_prediction) == len(nonlinear_prediction)):
        raise ValueError("Unpaired predictions")
    if any(int(v) not in {1, 2, 3, 4} for v in [*linear_prediction, *nonlinear_prediction]):
        raise ValueError("Only T1-T4 predictions")
    records = [
        dict(r, A_prediction=int(a), B_prediction=int(b))
        for r, a, b in zip(rows, linear_prediction, nonlinear_prediction, strict=True)
    ]
    result = summarize(records)
    result["arms"] = {"A": "linear", "B": "nonlinear"}
    result["per_speaker"] = {
        speaker: summarize([r for r in records if r["speaker_id"] == speaker])
        for speaker in sorted({r["speaker_id"] for r in records})
    }
    return result


def lock():
    OUT.mkdir(parents=True, exist_ok=True)
    old_lock = json.loads((OLD / "experiment-config.locked.json").read_text())
    if (old_lock["selected_layer"], old_lock["selected_C"]) != (8, 0.1):
        raise ValueError("Frozen baseline changed")
    if old_lock["model"]["revision"] != REVISION or old_lock["preprocessing"] != PREPROCESSING:
        raise ValueError("Encoder/preprocessing changed")
    rows = [r for r in authoritative_rows() if r["partition"] == "train"]
    validate_training(rows)
    paths = [
        CODE / n
        for n in (
            "nonlinear_head.py",
            "nonlinear_sources.py",
            "features.py",
            "model_probe.py",
            "temporal_pooling.py",
            "evaluation_preflight.py",
            "pilot.py",
            "preflight.py",
            "remediate.py",
            "requirements-lock.txt",
        )
    ] + [OUT / "protocol.md", OLD / "split-manifest.csv", OLD / "experiment-config.locked.json"]
    exclusive_json(
        OUT / "protocol.lock.json",
        dict(
            locked_at=now(),
            nonlinear=dict(CONFIG),
            linear=dict(CLASSIFIER),
            scaler=dict(SCALER),
            encoder=old_lock["model"],
            preprocessing=PREPROCESSING,
            layer=8,
            training_ids=[r["source_asset_id"] for r in rows],
            environment=environment(),
            files_sha256={str(p.relative_to(ROOT)): sha256(p) for p in paths},
            fresh_test_access=False,
            nonlinear_real_data_training=False,
        ),
    )


def verify_lock():
    receipt = json.loads((OUT / "protocol.lock.json").read_text())
    if receipt["nonlinear"] != dict(CONFIG) or receipt["linear"] != dict(CLASSIFIER):
        raise ValueError("Head configuration changed after lock")
    for name, expected in receipt["files_sha256"].items():
        if sha256(ROOT / name) != expected:
            raise ValueError(f"Locked input/code changed: {name}")
    if environment() != receipt["environment"]:
        raise ValueError("Locked environment changed")
    for name, expected in receipt["encoder"]["files_sha256"].items():
        if sha256(Path(receipt["encoder"]["snapshot"]) / name) != expected:
            raise ValueError("Pinned encoder bytes changed")
    return receipt


def reproduce():
    receipt = verify_lock()
    CACHE.mkdir(parents=True, exist_ok=True)
    exclusive_json(OUT / "baseline-started.json", dict(started_at=now()))
    rows = [r for r in authoritative_rows() if r["partition"] in {"train", "validation"}]
    original_lock = json.loads((OLD / "experiment-config.locked.json").read_text())
    for name, key in (
        ("development-features.npz", "development_features_sha256"),
        ("selected-head.npz", "head_sha256"),
    ):
        if sha256(OLD_CACHE / name) != original_lock[key]:
            raise ValueError("Original cached artifact changed")
    destination = CACHE / "reproduced-development.npz"
    extraction = extract(rows, receipt["encoder"]["snapshot"], destination, layers=(8,))
    fresh = np.load(destination, allow_pickle=False)
    original = np.load(OLD_CACHE / "development-features.npz", allow_pickle=False)
    np.testing.assert_array_equal(fresh["asset_ids"], original["asset_ids"])
    np.testing.assert_array_equal(fresh["layer_8"], original["layer_8"])
    arrays, fit = fit_fixed(fresh["layer_8"], rows, receipt["training_ids"])
    saved = np.load(OLD_CACHE / "selected-head.npz", allow_pickle=False)
    differences = {}
    for key in saved.files:
        np.testing.assert_array_equal(arrays[key], saved[key])
        differences[key] = float(np.max(np.abs(arrays[key] - saved[key])))
    head_path = OUT / "head-linear.npz"
    save_arrays(head_path, **arrays)
    mask = np.array([r["partition"] == "validation" for r in rows])
    a = predict_head(head_path, fresh["layer_8"][mask])
    b = predict_head(OLD_CACHE / "selected-head.npz", original["layer_8"][mask])
    np.testing.assert_array_equal(a, b)
    validation_rows = [r for r in rows if r["partition"] == "validation"]
    exclusive_json(
        OUT / "baseline-reproduction.json",
        dict(
            completed_at=now(),
            passed=True,
            feature_bitwise_equal=True,
            head_bitwise_equal=True,
            head_max_absolute_differences=differences,
            probabilities_bitwise_equal=True,
            predictions_identical=True,
            fit=fit,
            extraction=extraction,
            validation=comparison(validation_rows, a.argmax(1) + 1, b.argmax(1) + 1)["A"],
            artifacts_sha256={
                str(p.relative_to(ROOT)): sha256(p) for p in (destination, head_path)
            },
        ),
    )


def develop():
    """Next pass: fit final nonlinear head; do not read any evaluation features."""
    verify_lock()
    reproduction = json.loads((OUT / "baseline-reproduction.json").read_text())
    if not reproduction["passed"]:
        raise ValueError("Baseline reproduction required")
    for name, expected in reproduction["artifacts_sha256"].items():
        if sha256(ROOT / name) != expected:
            raise ValueError("Reproduction artifact changed")
    exclusive_json(OUT / "development-started.json", dict(started_at=now()))
    rows = [r for r in authoritative_rows() if r["partition"] in {"train", "validation"}]
    features = np.load(CACHE / "reproduced-development.npz", allow_pickle=False)
    np.testing.assert_array_equal(features["asset_ids"], [r["source_asset_id"] for r in rows])
    mask = np.array([r["partition"] == "train" for r in rows])
    arrays, losses = fit_nonlinear(
        features["layer_8"][mask], [r for r in rows if r["partition"] == "train"]
    )
    save_arrays(OUT / "head-nonlinear.npz", **arrays)
    exclusive_json(
        OUT / "heads.lock.json",
        dict(
            locked_at=now(),
            protocol_sha256=sha256(OUT / "protocol.lock.json"),
            heads_sha256={n: sha256(OUT / n) for n in ("head-linear.npz", "head-nonlinear.npz")},
            nonlinear_arrays_sha256=arrays_hash(arrays),
            epochs=len(losses),
            training_loss_first=losses[0],
            training_loss_last=losses[-1],
            evaluation_predictions_opened=False,
        ),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("lock", "verify", "reproduce", "develop"))
    args = parser.parse_args()
    {"lock": lock, "verify": verify_lock, "reproduce": reproduce, "develop": develop}[args.stage]()


if __name__ == "__main__":
    main()

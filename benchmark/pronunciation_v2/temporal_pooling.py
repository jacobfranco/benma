"""Experiment 2: fixed, sequential development -> lock -> fresh -> stress stages.

No acquisition or model selection. All model access follows the offline seal gate.
Feature caches, receipts, fitted parameters and result files refuse replacement.
"""

import argparse
import csv
import hashlib
import importlib.metadata
import json
import platform
import resource
import subprocess
import time
from itertools import pairwise
from pathlib import Path
from types import MappingProxyType

import numpy as np
import torch
from evaluation_preflight import temporal_bin_boundaries
from features import MODEL_ID, PREPROCESSING, freeze, load_waveform, masked_mean, state_digest
from model_probe import exclusive_json, metrics, now, predict_head, versions
from preflight import sha256
from remediate import validate_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits
from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2Model

ROOT = Path(__file__).resolve().parents[2]
CODE = Path(__file__).resolve().parent
OLD = ROOT / "docs/research/pronunciation-v2/2026-09-29-frozen-wav2vec"
PREFLIGHT = ROOT / "docs/research/pronunciation-v2/2026-09-30-experiment-2-preflight"
OUTPUT = ROOT / "docs/research/pronunciation-v2/2026-09-30-experiment-2-temporal-pooling"
CACHE = ROOT / "benchmark/corpus/recordings/original/experiment-2-temporal-cache"
OLD_CACHE = Path.home() / ".cache/benma/pronunciation-v2-model"
SEAL_HASH = "7e9ba24601a1199ad07f721e9ca9cb22ef5736095a0fdb2b44091aa143dce75d"
SPLIT_HASH = "1ee5ab2d6bbb6739e461c53949d699cef687d8b6e25412717400889f219e6416"
REVISION = "0b5b8e868dd84f03fd87d01f9c4ff0f080fecfe8"
TRAIN_SPEAKERS = frozenset(("shtooka:wei-gao", "lingualibre:Q1431140"))
CLASSIFIER = MappingProxyType(
    dict(
        C=0.1,
        solver="lbfgs",
        penalty="l2",
        class_weight=None,
        fit_intercept=True,
        max_iter=3000,
        tol=1e-8,
        random_state=20260929,
    )
)
SCALER = MappingProxyType(dict(copy=True, with_mean=True, with_std=True))
POOLING = MappingProxyType(
    dict(
        A="mean H[0:N]; 768 dimensions",
        B="concat means H[0:N//3], H[N//3:(2*N)//3], H[(2*N)//3:N]; 2304 dimensions",
        short="N < 3 fails BOTH arms; no padding/repetition/interpolation",
    )
)
# Fixed before any reproduction/result access; predictions must match exactly too.
REPRO_ATOL = 1e-10


def csv_rows(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def exclusive_csv(path, rows):
    with path.open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def save_arrays(path, **arrays):
    with path.open("xb") as handle:
        np.savez_compressed(handle, **arrays)


def arrays_hash(arrays):
    digest = hashlib.sha256()
    for key, value in sorted(arrays.items()):
        value = np.ascontiguousarray(value)
        digest.update(json.dumps([key, value.dtype.str, list(value.shape)]).encode())
        digest.update(value.tobytes())
    return digest.hexdigest()


def verify_seal():
    subprocess.run(
        [
            str(ROOT / "services/api/.venv/bin/python"),
            str(CODE / "evaluation_preflight.py"),
            "verify",
        ],
        cwd=ROOT,
        check=True,
    )
    if sha256(PREFLIGHT / "sealed-test-manifest.csv") != SEAL_HASH:
        raise ValueError("Sealed manifest differs from explicitly authorized SHA-256")
    rows = csv_rows(PREFLIGHT / "sealed-test-manifest.csv")
    if len(rows) != 118:
        raise ValueError("Expected exactly 118 sealed rows")
    return rows


def validate_training(rows, fresh):
    validate_split(rows)
    train = [r for r in rows if r["partition"] == "train"]
    if len(train) != 386 or {r["speaker_id"] for r in train} != TRAIN_SPEAKERS:
        raise ValueError("Primary training membership changed")
    for key in ("source_asset_id", "speaker_id", "audio_sha256", "decoded_pcm_sha256"):
        if {r[key] for r in rows} & {r[key] for r in fresh}:
            raise ValueError(f"Fresh evaluation overlaps historical corpus: {key}")
    return train


def environment():
    packages = {}
    for line in (CODE / "requirements-lock.txt").read_text().splitlines():
        name, expected = line.split("==")
        observed = importlib.metadata.version(name)
        if observed != expected:
            raise ValueError(f"Pinned dependency changed: {name}")
        packages[name] = observed
    return dict(
        python=platform.python_version(),
        platform=platform.platform(),
        packages=packages,
        versions=versions(),
        ffmpeg=subprocess.check_output(["ffmpeg", "-version"], text=True).splitlines()[0],
        torch_threads=4,
        blas_fit_threads=1,
        device="cpu",
        dtype="float32",
    )


def source_hashes():
    names = (
        "temporal_pooling.py",
        "test_temporal_pooling.py",
        "features.py",
        "model_probe.py",
        "evaluation_preflight.py",
        "pilot.py",
        "preflight.py",
        "remediate.py",
        "requirements.txt",
        "requirements-lock.txt",
    )
    return {str((CODE / n).relative_to(ROOT)): sha256(CODE / n) for n in names}


def input_hashes():
    paths = [
        OLD / n
        for n in (
            "split-manifest.csv",
            "experiment-config.locked.json",
            "validation-results.csv",
            "checkpoint.json",
        )
    ]
    paths += [PREFLIGHT / n for n in ("sealed-test-manifest.csv", "seal.json", "protocol.md")]
    return {str(p.relative_to(ROOT)): sha256(p) for p in paths}


def prerequisites():
    fresh = verify_seal()  # Always before loading checkpoint/old fitted head/feature cache.
    if sha256(OLD / "split-manifest.csv") != SPLIT_HASH:
        raise ValueError("Original split changed")
    rows = csv_rows(OLD / "split-manifest.csv")
    validate_training(rows, fresh)
    old_lock = json.loads((OLD / "experiment-config.locked.json").read_text())
    if (old_lock["selected_layer"], old_lock["selected_C"]) != (8, 0.1):
        raise ValueError("Authoritative baseline differs")
    checkpoint = old_lock["model"]
    if checkpoint["model_id"] != MODEL_ID or checkpoint["revision"] != REVISION:
        raise ValueError("Wrong encoder")
    for name, expected in checkpoint["files_sha256"].items():
        if sha256(Path(checkpoint["snapshot"]) / name) != expected:
            raise ValueError("Checkpoint bytes changed")
    return rows, fresh, old_lock, environment()


def pool_frames(hidden):
    """Input is ONLY valid chronological frames from a single unpadded forward."""
    if hidden.ndim != 2 or not torch.isfinite(hidden).all():
        raise ValueError("Expected finite N x hidden_size valid frames")
    bounds = temporal_bin_boundaries(hidden.shape[0])
    # Same arithmetic/reduction as Experiment 1 for bitwise baseline reproduction.
    a = masked_mean(hidden[None], torch.ones((1, len(hidden)), dtype=torch.bool))[0]
    b = torch.cat([hidden[start:end].mean(0) for start, end in pairwise(bounds)])
    return {"A": a.cpu().numpy(), "B": b.cpu().numpy()}


def encode_pair(model, processor, wave):
    if model.training or any(p.requires_grad for p in model.parameters()):
        raise ValueError("Encoder must be frozen")
    if any(p.device.type != "cpu" or p.dtype != torch.float32 for p in model.parameters()):
        raise ValueError("CPU FP32 required")
    with torch.inference_mode():
        values = processor(wave, sampling_rate=16000, return_tensors="pt").input_values
        states = model(values, output_hidden_states=True).hidden_states
        hidden = states[8][0]
        result = pool_frames(hidden)
    if any(p.grad is not None for p in model.parameters()):
        raise RuntimeError("Unexpected encoder gradients")
    return result, len(hidden)


def extract_pairs(rows, checkpoint, destination):
    if destination.exists():
        raise FileExistsError("Refusing replacement of pooled feature cache")
    started = time.perf_counter()
    torch.set_num_threads(4)
    torch.manual_seed(20260929)
    torch.use_deterministic_algorithms(True)
    model, loading = Wav2Vec2Model.from_pretrained(
        checkpoint["snapshot"],
        local_files_only=True,
        attn_implementation="eager",
        output_loading_info=True,
    )
    if loading["missing_keys"] or loading["mismatched_keys"] or loading["error_msgs"]:
        raise RuntimeError(f"Incomplete checkpoint: {loading}")
    model = freeze(model.cpu().float())
    if model.config.hidden_size != 768:
        raise ValueError("Expected 768 hidden dimensions")
    processor = Wav2Vec2FeatureExtractor.from_pretrained(
        checkpoint["snapshot"], local_files_only=True
    )
    before = state_digest(model)
    collected, frames = {"A": [], "B": []}, []
    for i, row in enumerate(rows, 1):
        path = Path(row["local_path"])
        if sha256(path) != row["audio_sha256"]:
            raise ValueError("Audio bytes changed")
        wave = load_waveform(path)
        pair, n = encode_pair(model, processor, wave)
        if i == 1:
            repeat, repeat_n = encode_pair(model, processor, wave)
            if n != repeat_n or not all(np.array_equal(pair[a], repeat[a]) for a in pair):
                raise RuntimeError("Nondeterministic extraction")
        for arm in collected:
            collected[arm].append(pair[arm])
        frames.append(n)
        if i % 50 == 0:
            print(f"Extracted both arms {i}/{len(rows)}", flush=True)
    after = state_digest(model)
    if before != after or any(p.grad is not None for p in model.parameters()):
        raise RuntimeError("Frozen encoder mutated")
    arrays = {a: np.stack(v) for a, v in collected.items()}
    save_arrays(
        destination, asset_ids=[r["source_asset_id"] for r in rows], frames=frames, **arrays
    )
    return dict(
        n=len(rows),
        seconds=time.perf_counter() - started,
        peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
        state_hash_before=before,
        state_hash_after=after,
        no_gradients=True,
        first_clip_repeat_bitwise_equal=True,
        min_frames=min(frames),
        max_frames=max(frames),
        dimensions={a: x.shape[1] for a, x in arrays.items()},
        loading_info=loading,
        feature_cache=str(destination),
        feature_cache_sha256=sha256(destination),
        processor_config=processor.to_dict(),
    )


def fit_fixed(x, rows, training_ids):
    ids = [r["source_asset_id"] for r in rows]
    if len(ids) != len(set(ids)) or len(x) != len(rows):
        raise ValueError("Duplicate/misaligned training candidates")
    if not training_ids or not set(training_ids) <= set(ids):
        raise ValueError("Unknown training IDs")
    selected = np.array([i in training_ids for i in ids])
    if any(
        r["partition"] != "train" or r["speaker_id"] not in TRAIN_SPEAKERS
        for r, use in zip(rows, selected, strict=True)
        if use
    ):
        raise ValueError("Evaluation row entering fitting")
    scaler = StandardScaler(**SCALER).fit(x[selected])
    y = np.array([int(r["tone"]) for r in rows])[selected]
    with threadpool_limits(limits=1):
        model = LogisticRegression(**CLASSIFIER).fit(scaler.transform(x[selected]), y)
    if model.n_iter_.max() >= CLASSIFIER["max_iter"]:
        raise RuntimeError("Fixed classifier failed to converge; no retuning permitted")
    if not np.array_equal(model.classes_, [1, 2, 3, 4]):
        raise ValueError("Expected four classes")
    arrays = dict(
        mean=scaler.mean_,
        var=scaler.var_,
        scale=scaler.scale_,
        n_samples_seen=np.asarray(scaler.n_samples_seen_),
        coef=model.coef_,
        intercept=model.intercept_,
        classes=model.classes_,
    )
    return arrays, dict(
        dimensions=x.shape[1],
        training_rows=int(selected.sum()),
        iterations=int(model.n_iter_.max()),
        training_ids=[i for i, use in zip(ids, selected, strict=True) if use],
        scaler_sha256=arrays_hash(
            {k: arrays[k] for k in ("mean", "var", "scale", "n_samples_seen")}
        ),
        classifier_sha256=arrays_hash({k: arrays[k] for k in ("coef", "intercept", "classes")}),
        scaler_config=dict(SCALER),
        classifier_config=dict(CLASSIFIER),
        classifier_all_parameters=model.get_params(),
        multiclass_objective="multinomial (4 classes)",
    )


def detailed_metrics(rows, prediction):
    result = metrics([int(r["tone"]) for r in rows], prediction)
    if any(v["support"] == 0 for v in result["per_tone"].values()):
        result["balanced_accuracy"] = None
    matrix = result["confusion_matrix"]
    result["directed_confusions"] = {
        f"T{a}->T{b}": dict(
            count=matrix[a - 1][b - 1],
            rate=matrix[a - 1][b - 1] / result["per_tone"][str(a)]["support"]
            if result["per_tone"][str(a)]["support"]
            else None,
        )
        for a, b in ((2, 3), (3, 2), (3, 4), (4, 3))
    }
    result["bidirectional_confusions"] = {
        "T2<->T3": matrix[1][2] + matrix[2][1],
        "T3<->T4": matrix[2][3] + matrix[3][2],
    }
    return result


def summarize(records):
    if len({r["source_asset_id"] for r in records}) != len(records):
        raise ValueError("Duplicate prediction IDs")
    result = {a: detailed_metrics(records, [r[f"{a}_prediction"] for r in records]) for a in "AB"}
    counts = dict(both_correct=0, A_only_correct=0, B_only_correct=0, both_wrong=0)
    for r in records:
        a, b = (r[f"{arm}_prediction"] == int(r["tone"]) for arm in "AB")
        counts[
            "both_correct"
            if a and b
            else "A_only_correct"
            if a
            else "B_only_correct"
            if b
            else "both_wrong"
        ] += 1
    result["paired_correctness"] = counts
    result["B_minus_A"] = {
        k: result["B"][k] - result["A"][k]
        for k in ("accuracy", "balanced_accuracy", "macro_f1")
        if result["A"][k] is not None
    }
    return result


def evaluate(rows, features, heads):
    ids = [r["source_asset_id"] for r in rows]
    if not np.array_equal(features["asset_ids"], ids):
        raise ValueError("Feature/prediction row membership mismatch")
    probabilities = {a: predict_head(heads[a], features[a]) for a in "AB"}
    if any(p.shape != (len(rows), 4) for p in probabilities.values()):
        raise ValueError("Both arms must predict every identical clip ID")
    records = []
    for i, row in enumerate(rows):
        record = {
            k: row[k]
            for k in ("source_asset_id", "speaker_id", "speaker_name", "text", "pinyin", "tone")
        }
        for arm, p in probabilities.items():
            record.update(
                {
                    f"{arm}_prediction": int(p[i].argmax()) + 1,
                    f"{arm}_confidence": float(p[i].max()),
                    f"{arm}_correct": int(p[i].argmax()) + 1 == int(row["tone"]),
                    **{f"{arm}_p_T{t}": float(p[i, t - 1]) for t in range(1, 5)},
                }
            )
        records.append(record)
    report = summarize(records)
    report["per_speaker"] = {
        name: summarize([r for r in records if r["speaker_name"] == name])
        for name in sorted({r["speaker_name"] for r in rows})
    }
    report["equal_speaker_mean"] = {
        a: {
            k: float(np.mean([s[a][k] for s in report["per_speaker"].values()]))
            for k in ("accuracy", "balanced_accuracy", "macro_f1")
        }
        for a in "AB"
    }
    report["confidence"] = "uncalibrated maximum softmax; no rejection threshold"
    return report, records


def reproduce(features, rows, head, old_lock):
    for name, key in (
        ("development-features.npz", "development_features_sha256"),
        ("selected-head.npz", "head_sha256"),
    ):
        if sha256(OLD_CACHE / name) != old_lock[key]:
            raise ValueError("Authoritative Experiment 1 cached artifact changed")
    if sha256(OLD / "validation-results.csv") != old_lock["validation_results_sha256"]:
        raise ValueError("Authoritative validation metrics changed")
    original = np.load(OLD_CACHE / "development-features.npz", allow_pickle=False)
    if not np.array_equal(original["asset_ids"], features["asset_ids"]):
        raise ValueError("Development row ordering differs")
    np.testing.assert_allclose(features["A"], original["layer_8"], rtol=0, atol=REPRO_ATOL)
    saved = np.load(OLD_CACHE / "selected-head.npz", allow_pickle=False)
    differences = {}
    for key in saved.files:
        np.testing.assert_allclose(head[key], saved[key], rtol=0, atol=REPRO_ATOL)
        differences[key] = float(np.max(np.abs(head[key] - saved[key])))
    mask = np.array([r["partition"] == "validation" for r in rows])
    a = predict_head(OUTPUT / "head-A.npz", features["A"][mask])
    b = predict_head(OLD_CACHE / "selected-head.npz", original["layer_8"][mask])
    np.testing.assert_allclose(a, b, rtol=0, atol=REPRO_ATOL)
    np.testing.assert_array_equal(a.argmax(1), b.argmax(1))
    measured = metrics(
        [int(r["tone"]) for r in rows if r["partition"] == "validation"], a.argmax(1) + 1
    )
    reference = next(
        r for r in csv_rows(OLD / "validation-results.csv") if r["layer"] == "8" and r["C"] == "0.1"
    )
    for key in ("accuracy", "balanced_accuracy", "macro_f1"):
        np.testing.assert_allclose(measured[key], float(reference[key]), rtol=0, atol=1e-12)
    return dict(
        passed=True,
        completed_at=now(),
        absolute_tolerance=REPRO_ATOL,
        feature_bitwise_equal=bool(np.array_equal(features["A"], original["layer_8"])),
        feature_max_absolute_difference=float(np.max(np.abs(features["A"] - original["layer_8"]))),
        head_max_absolute_differences=differences,
        probability_max_absolute_difference=float(np.max(np.abs(a - b))),
        predictions_identical=True,
        validation_metrics=measured,
        authoritative_artifacts={
            str(OLD_CACHE / n): sha256(OLD_CACHE / n)
            for n in ("selected-head.npz", "development-features.npz")
        },
    )


def subset_features(features, mask):
    return {k: features[k][mask] for k in ("asset_ids", "A", "B")}


def develop():
    rows, fresh, old_lock, env = prerequisites()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    exclusive_json(
        OUTPUT / "development-started.json",
        dict(
            started_at=now(),
            seal_verified=True,
            source_code_sha256=source_hashes(),
            inputs=input_hashes(),
        ),
    )
    development = [r for r in rows if r["partition"] in ("train", "validation")]
    train = validate_training(rows, fresh)
    exclusive_csv(OUTPUT / "training-manifest.csv", train)
    extraction = extract_pairs(development, old_lock["model"], CACHE / "development.npz")
    exclusive_json(OUTPUT / "development-extraction.json", extraction)
    features = np.load(CACHE / "development.npz", allow_pickle=False)
    train_ids = {r["source_asset_id"] for r in train}
    heads, details = {}, {}
    for arm in "AB":
        arrays, details[arm] = fit_fixed(features[arm], development, train_ids)
        heads[arm] = OUTPUT / f"head-{arm}.npz"
        save_arrays(heads[arm], **arrays)
        details[arm]["file_sha256"] = sha256(heads[arm])
        if arm == "A":
            try:
                reproduction = reproduce(features, development, arrays, old_lock)
            except Exception as error:
                exclusive_json(
                    OUTPUT / "baseline-reproduction-failure.json",
                    dict(at=now(), error=repr(error), test_opened=False),
                )
                raise
            exclusive_json(OUTPUT / "baseline-reproduction.json", reproduction)
            print("Baseline A reproduced before fitting B or opening fresh test", flush=True)
    validation_mask = np.array([r["partition"] == "validation" for r in development])
    validation = [r for r, use in zip(development, validation_mask, strict=True) if use]
    report, predictions = evaluate(validation, subset_features(features, validation_mask), heads)
    exclusive_csv(OUTPUT / "development-predictions.csv", predictions)
    diagnostics = {}
    for name, speaker in (
        ("Wei_Gao_only", "shtooka:wei-gao"),
        ("CanonNi_only", "lingualibre:Q1431140"),
    ):
        diagnostic_ids = {r["source_asset_id"] for r in train if r["speaker_id"] == speaker}
        mask = np.array(
            [
                r["speaker_id"] != speaker
                and (speaker == "shtooka:wei-gao" or r["partition"] == "train")
                for r in development
            ]
        )
        held = [r for r, use in zip(development, mask, strict=True) if use]
        diagnostic_heads, metadata = {}, {}
        for arm in "AB":
            arrays, metadata[arm] = fit_fixed(features[arm], development, diagnostic_ids)
            path = CACHE / f"{name}-{arm}.npz"
            save_arrays(path, **arrays)
            diagnostic_heads[arm] = path
            metadata[arm].update(file=str(path), file_sha256=sha256(path))
        diagnostic, records = evaluate(held, subset_features(features, mask), diagnostic_heads)
        diagnostics[name] = dict(results=diagnostic, fits=metadata)
        exclusive_csv(OUTPUT / f"development-{name}-predictions.csv", records)
    exclusive_json(
        OUTPUT / "development-results.json",
        dict(
            validation=report,
            source_diagnostics=diagnostics,
            fits=details,
            baseline_reproduction=reproduction,
            completed_at=now(),
            environment=env,
            scope="Previously inspected development diagnostics; no selection or tuning",
        ),
    )
    print(json.dumps({a: report[a] for a in "AB"}, indent=2), flush=True)


def lock():
    _, _, old_lock, env = prerequisites()
    started = json.loads((OUTPUT / "development-started.json").read_text())
    if started["source_code_sha256"] != source_hashes() or started["inputs"] != input_hashes():
        raise ValueError("Implementation/inputs changed during development")
    development = json.loads((OUTPUT / "development-results.json").read_text())
    if not development["baseline_reproduction"]["passed"] or development["environment"] != env:
        raise ValueError("Development reproduction/environment gate failed")
    fitted = development["fits"]
    for arm in "AB":
        if sha256(OUTPUT / f"head-{arm}.npz") != fitted[arm]["file_sha256"]:
            raise ValueError("Fitted primary head changed")
    payload = dict(
        locked_at=now(),
        git_HEAD=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        encoder=old_lock["model"],
        preprocessing=dict(PREPROCESSING),
        hidden_layer=8,
        hidden_layer_indexing="output after Transformer block 8",
        pooling=dict(POOLING),
        training_row_count=386,
        train_manifest_sha256=sha256(OUTPUT / "training-manifest.csv"),
        scaler_config=dict(SCALER),
        classifier_config=dict(CLASSIFIER),
        fitted=fitted,
        development_metrics=development,
        source_code_sha256=source_hashes(),
        inputs=input_hashes(),
        sealed_test_manifest_expected_sha256=SEAL_HASH,
        environment=env,
        development_artifact_sha256={
            p.name: sha256(p) for p in sorted(OUTPUT.iterdir()) if p.is_file()
        },
        fresh_test_opened=False,
        policy=(
            "No configuration changes or silent replacement after opening; "
            "corrective reruns explicit"
        ),
    )
    exclusive_json(OUTPUT / "lock.json", payload)
    print(json.dumps(dict(locked_at=payload["locked_at"], sha256=sha256(OUTPUT / "lock.json"))))


def require_lock(env):
    locked = json.loads((OUTPUT / "lock.json").read_text())
    if (
        locked["source_code_sha256"] != source_hashes()
        or locked["inputs"] != input_hashes()
        or locked["environment"] != env
        or locked["classifier_config"] != dict(CLASSIFIER)
        or locked["scaler_config"] != dict(SCALER)
        or locked["pooling"] != dict(POOLING)
    ):
        raise ValueError("Locked implementation, inputs, environment or configuration changed")
    for name, expected in locked["development_artifact_sha256"].items():
        if sha256(OUTPUT / name) != expected:
            raise ValueError(f"Locked development artifact changed: {name}")
    return locked


def run_panel(stage):
    rows, fresh, _, env = prerequisites()
    locked = require_lock(env)
    if stage == "stress":
        receipt = json.loads((OUTPUT / "fresh-test-completed.json").read_text())
        for name, expected in receipt["artifacts"].items():
            if sha256(OUTPUT / name) != expected:
                raise ValueError("Fresh result changed before stress evaluation")
        selected = [r for r in rows if r["partition"] == "test"]
        if len(selected) != 60 or {r["speaker_name"] for r in selected} != {"Luilui6666"}:
            raise ValueError("Original Luilui stress set changed")
        prefix, scope = "stress", "KNOWN / INSPECTED STRESS SET; NOT pristine test data"
    else:
        selected, prefix = fresh, "fresh-test"
        scope = (
            "Fresh speaker panel; UNKNOWN native status; "
            "lexical targets, not verified realized tones"
        )
    exclusive_json(
        OUTPUT / f"{prefix}-opened.json",
        dict(
            opened_at=now(),
            lock_sha256=sha256(OUTPUT / "lock.json"),
            n=len(selected),
            sealed_manifest_sha256=SEAL_HASH,
            scope=scope,
            seal_verified_before_evaluation=True,
        ),
    )
    extraction = extract_pairs(selected, locked["encoder"], CACHE / f"{prefix}.npz")
    exclusive_json(OUTPUT / f"{prefix}-extraction.json", extraction)
    report, records = evaluate(
        selected,
        np.load(CACHE / f"{prefix}.npz", allow_pickle=False),
        {a: OUTPUT / f"head-{a}.npz" for a in "AB"},
    )
    report.update(scope=scope, lock_sha256=sha256(OUTPUT / "lock.json"), completed_at=now())
    if stage == "stress":
        t3 = [r for r in records if int(r["tone"]) == 3]
        if len(t3) != 13:
            raise ValueError("Expected original 13 T3 cases")
        report["T3_subset"] = {
            a: dict(
                n=13,
                correct=sum(r[f"{a}_correct"] for r in t3),
                recall=sum(r[f"{a}_correct"] for r in t3) / 13,
                prediction_counts={
                    str(t): sum(r[f"{a}_prediction"] == t for r in t3) for t in range(1, 5)
                },
            )
            for a in "AB"
        }
        report["T3_cases"] = t3
    exclusive_csv(OUTPUT / f"{prefix}-predictions.csv", records)
    exclusive_json(OUTPUT / f"{prefix}-results.json", report)
    exclusive_json(
        OUTPUT / f"{prefix}-completed.json",
        dict(
            completed_at=now(),
            artifacts={
                f"{prefix}-{suffix}": sha256(OUTPUT / f"{prefix}-{suffix}")
                for suffix in ("results.json", "predictions.csv", "opened.json", "extraction.json")
            },
        ),
    )
    print(json.dumps(report, indent=2, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("develop", "lock", "fresh", "stress"))
    args = parser.parse_args()
    if args.stage == "develop":
        develop()
    elif args.stage == "lock":
        lock()
    else:
        run_panel(args.stage)


if __name__ == "__main__":
    main()

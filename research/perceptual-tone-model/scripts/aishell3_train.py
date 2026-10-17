"""Write-once AISHELL-3 train/validation selection, then sealed test evaluation."""

import argparse
import copy
import json
import subprocess
import sys
import warnings
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
from sklearn.utils.class_weight import compute_sample_weight
from threadpoolctl import threadpool_limits

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aishell3_release import VERSION, verify_release
from perceptual_tone.aishell3_embeddings import LAYERS, Encoder, canonical_audio
from perceptual_tone.aishell3_learning import (
    CLASSES,
    acoustic_vector,
    audio_contract,
    label_mutation_check,
    metric,
    pipeline,
)
from perceptual_tone.common import (
    PACKAGE,
    ROOT,
    file_hash,
    read_json,
    read_rows,
    runtime,
    write_json,
)
from perceptual_tone.manifest import verify_baseline

DEFAULT_RELEASE = PACKAGE / "data/generated/aishell3/releases" / VERSION
DEFAULT_RUN = PACKAGE / "models/generated/aishell3-first-four-tone-v1"


def now():
    return datetime.now(UTC).isoformat()


def probabilities(model, matrix):
    if tuple(model.classes_) != CLASSES:
        raise ValueError("class_order_changed")
    return model.predict_proba(matrix)


def evaluate(model, matrix, labels):
    prob = probabilities(model, matrix)
    pred = np.asarray(CLASSES)[prob.argmax(1)]
    return metric(labels, pred, prob), prob


def acoustics(rows, folder):
    output = folder / "acoustic-baseline.json"
    seal = folder / "acoustic-seal.json"
    if output.exists():
        if file_hash(output) != read_json(seal)["sha256"]:
            raise ValueError("acoustic_cache_changed")
        return read_json(output)
    utterances = {}
    for row in rows:
        contract = audio_contract(row)
        source = canonical_audio(
            contract["audio_reference"], contract["audio_sha256"], folder / "canonical"
        )
        item = utterances.setdefault(
            str(source), {"audio_path": str(source), "audio_sha256": file_hash(source), "units": []}
        )
        item["units"].append(
            {
                "example_id": row["example_id"],
                "start": contract["read_unit"][0],
                "end": contract["read_unit"][1],
            }
        )
    spec = folder / "acoustic-input.json"
    write_json(spec, list(utterances.values()))
    raw = folder / "acoustic-raw.json"
    subprocess.run(
        [
            str(ROOT / "services/api/.venv/bin/python"),
            str(PACKAGE / "scripts/aishell3_acoustics.py"),
            str(spec),
            str(raw),
        ],
        check=True,
    )
    subprocess.run(
        ["node", str(PACKAGE / "aishell3_acoustic_baseline.cjs"), str(raw), str(output)], check=True
    )
    write_json(
        seal,
        {
            "sha256": file_hash(output),
            "raw_sha256": file_hash(raw),
            "input_sha256": file_hash(spec),
            "created": now(),
        },
    )
    return read_json(output)


def embeddings(rows, encoder_name, view, folder, phase):
    destination = folder / f"{phase}-{encoder_name}-{view}.npz"
    seal = destination.with_suffix(".json")
    ids = [r["example_id"] for r in rows]
    if destination.exists():
        record = read_json(seal)
        if record["ids"] != ids or record["sha256"] != file_hash(destination):
            raise ValueError("matrix_cache_changed")
        return np.load(destination, allow_pickle=False)["values"]
    encoder = Encoder(encoder_name, folder / "embedding-cache", folder / "canonical")
    vectors, records = [], []
    for index, row in enumerate(rows):
        result, record = encoder.extract(audio_contract(row), view)
        vectors.append(result)
        records.append(
            {
                "example_id": row["example_id"],
                "key": record["key"],
                "owned_frames": record["owned_frames"],
            }
        )
        if (index + 1) % 50 == 0 or index == len(rows) - 1:
            print(f"{phase} {encoder_name} {view}: {index + 1}/{len(rows)}", flush=True)
    # Actual encoder cache reuse plus metadata mutation must give identical vectors.
    mutated = copy.deepcopy(rows[0])
    mutated["original"].update(label="T4", corpus_pinyin="LEAK4", hanzi="泄漏", expected_tone="T4")
    repeat, _ = encoder.extract(audio_contract(mutated), view)
    np.testing.assert_array_equal(repeat, vectors[0])
    values = np.stack(vectors)
    with destination.open("xb") as stream:
        np.savez_compressed(stream, values=values)
    write_json(
        seal,
        {
            "ids": ids,
            "sha256": file_hash(destination),
            "encoder": encoder.identity,
            "records": records,
            "cache_hits": encoder.hits,
            "cache_misses": encoder.misses,
            "mutation_cache_repeat_exact": True,
        },
    )
    return values


def feature_matrix(config, rows, acoustic, embedded):
    kind = config["features"]
    blocks = []
    if kind in ("embedding", "embedding_acoustics"):
        block = embedded[(config["encoder"], config["view"])]
        blocks.append(block[:, LAYERS.index(config["layer"]), :])
    if kind in ("acoustic", "embedding_acoustics"):
        blocks.append(np.stack([acoustic_vector(acoustic[r["example_id"]])[1] for r in rows]))
    if not blocks:
        raise ValueError("unsupported_feature_schema")
    return np.concatenate(blocks, axis=1)


def rank(entry):
    m = entry["validation"]
    return m["macro_f1"], m["balanced_accuracy"], m["accuracy"]


def select(rows, acoustic, folder, config):
    if (folder / "selected.json").exists():
        selected = read_json(folder / "selected.json")
        for item in selected["models"].values():
            if file_hash(folder / item["file"]) != item["sha256"]:
                raise ValueError("selected_model_changed")
        return selected
    # Neither test features nor test labels are used in this phase.
    rows = [r for r in rows if r["original"]["partition"] != "test"]
    is_train = np.array([r["original"]["partition"] == "train" for r in rows])
    labels = np.array([r["original"]["label"] for r in rows])
    embedded = {
        (name, view): embeddings(rows, name, view, folder, "selection")
        for name in config["encoders"]
        for view in config["views"]
    }
    trials, winners, models = [], {}, {}

    def fit(family, setting):
        matrix = feature_matrix(setting, rows, acoustic, embedded)
        model = pipeline(setting["kind"], setting.get("C", 1.0))
        kwargs = (
            {"mlpclassifier__sample_weight": compute_sample_weight("balanced", labels[is_train])}
            if setting["kind"] == "mlp"
            else {}
        )
        with warnings.catch_warnings(record=True) as captured, threadpool_limits(limits=4):
            warnings.simplefilter("always")
            model.fit(matrix[is_train], labels[is_train], **kwargs)
        train, _ = evaluate(model, matrix[is_train], labels[is_train])
        validation, prob = evaluate(model, matrix[~is_train], labels[~is_train])
        entry = {
            "trial": len(trials),
            "family": family,
            "config": setting,
            "train": train,
            "validation": validation,
            "warnings": [str(w.message) for w in captured],
            "feature_dimensions": matrix.shape[1],
        }
        trials.append(entry)
        if family not in winners or rank(entry) > rank(winners[family]):
            winners[family], models[family] = entry, (model, matrix[~is_train], prob)
        print(
            f"trial {entry['trial']} {family} {setting}: val F1={validation['macro_f1']:.4f}",
            flush=True,
        )

    for c in config["logistic_C"]:
        fit("model1_acoustic", {"features": "acoustic", "kind": "logistic", "C": c})
    for name in config["encoders"]:
        family = "model2_hubert" if name == "chinese_hubert_base" else "model3_wavlm"
        for view in config["views"]:
            for layer in config["layers"]:
                for c in config["logistic_C"]:
                    fit(
                        family,
                        {
                            "features": "embedding",
                            "kind": "logistic",
                            "encoder": name,
                            "view": view,
                            "layer": layer,
                            "C": c,
                        },
                    )
    speech = max(("model2_hubert", "model3_wavlm"), key=lambda x: rank(winners[x]))
    representation = {k: v for k, v in winners[speech]["config"].items() if k not in ("kind", "C")}
    fit("model4_mlp", {**representation, "kind": "mlp"})
    if config["optional_embedding_plus_acoustics"]:
        for c in config["logistic_C"]:
            fit(
                "model6_combined",
                {**representation, "features": "embedding_acoustics", "kind": "logistic", "C": c},
            )
    write_json(folder / "validation-trials.json", trials)
    chosen = {}
    for family, entry in winners.items():
        model, matrix, prob = models[family]
        file = family + ".joblib"
        with (folder / file).open("xb") as stream:
            joblib.dump(model, stream)
        reloaded = probabilities(joblib.load(folder / file), matrix)
        np.testing.assert_allclose(reloaded, prob, rtol=0, atol=1e-12)
        chosen[family] = {
            **entry,
            "file": file,
            "sha256": file_hash(folder / file),
            "reload_max_probability_delta": float(np.max(np.abs(reloaded - prob))),
        }
    best = max(winners, key=lambda x: rank(winners[x]))
    selected = {
        "frozen_at": now(),
        "best_family_by_validation": best,
        "best_speech_family_by_validation": speech,
        "models": chosen,
        "validation_trials_sha256": file_hash(folder / "validation-trials.json"),
        "protocol_sha256": file_hash(folder / "protocol.json"),
        "test_metrics_seen": False,
        "refit_on_validation": False,
    }
    write_json(folder / "selected.json", selected)
    print("CONFIGURATION/MODEL FREEZE: " + best, flush=True)
    return selected


def test(rows, acoustic, folder, selected):
    if (folder / "test-seal.json").exists():
        seal = read_json(folder / "test-seal.json")
        for file, sha in seal["files"].items():
            if file_hash(folder / file) != sha:
                raise ValueError("test_result_changed")
        return read_json(folder / "test-results.json")
    if file_hash(folder / "selected.json") == "":
        raise ValueError("missing_selection_freeze")
    test_rows = [r for r in rows if r["original"]["partition"] == "test"]
    labels = [r["original"]["label"] for r in test_rows]
    needed = sorted(
        {
            (v["config"]["encoder"], v["config"]["view"])
            for v in selected["models"].values()
            if "encoder" in v["config"]
        }
    )
    embedded = {
        (name, view): embeddings(test_rows, name, view, folder, "test") for name, view in needed
    }
    predictions, scores, per_speaker = {}, {}, {}
    baseline = [acoustic[r["example_id"]]["prediction"] for r in test_rows]
    predictions["model0_benma"] = [
        {
            "example_id": r["example_id"],
            "truth": labels[i],
            "prediction": baseline[i],
            "probabilities": None,
        }
        for i, r in enumerate(test_rows)
    ]
    scores["model0_benma"] = metric(labels, baseline)
    for family, item in selected["models"].items():
        matrix = feature_matrix(item["config"], test_rows, acoustic, embedded)
        model = joblib.load(folder / item["file"])
        score, prob = evaluate(model, matrix, labels)
        # A second reload produces identical selected test predictions.
        repeat = probabilities(joblib.load(folder / item["file"]), matrix)
        np.testing.assert_allclose(prob, repeat, rtol=0, atol=1e-12)
        scores[family] = {
            **score,
            "test_reload_max_probability_delta": float(np.max(np.abs(prob - repeat))),
        }
        predictions[family] = [
            {
                "example_id": r["example_id"],
                "truth": labels[i],
                "prediction": CLASSES[prob[i].argmax()],
                "probabilities": prob[i].tolist(),
            }
            for i, r in enumerate(test_rows)
        ]
        mask = np.array([x is not None for x in baseline])
        scores[family]["on_baseline_covered"] = metric(
            np.array(labels)[mask], np.array(CLASSES)[prob[mask].argmax(1)], prob[mask]
        )
    for family, values in predictions.items():
        per_speaker[family] = {}
        for speaker in sorted({r["original"]["speaker_id"] for r in test_rows}):
            subset = [
                values[i] for i, r in enumerate(test_rows) if r["original"]["speaker_id"] == speaker
            ]
            per_speaker[family][speaker] = metric(
                [r["truth"] for r in subset],
                [r["prediction"] for r in subset],
                [r["probabilities"] for r in subset] if family != "model0_benma" else None,
            )
    best = selected["best_family_by_validation"]
    errors = []
    for i, (row, pred) in enumerate(zip(test_rows, predictions[best], strict=True)):
        if pred["truth"] == pred["prediction"]:
            continue
        o = row["original"]
        span = row["spans"]["tone_bearing_pooling_span"]
        duration = span["end_seconds"] - span["start_seconds"]
        confidence = max(pred["probabilities"])
        categories = [pred["truth"] + "->" + pred["prediction"]]
        if o["following"] is None:
            categories.append("utterance-final")
        if duration < 0.06:
            categories.append("short-pooling-span")
        if confidence < 0.6:
            categories.append("low-confidence")
        if confidence >= 0.8:
            categories.append("high-confidence-error")
        errors.append(
            {
                **pred,
                "speaker": o["speaker_id"],
                "utterance": o["utterance_id"],
                "index": o["index"],
                "hanzi": o["hanzi"],
                "phonetic_base": o["phonetic_base"],
                "target_duration": o["end"] - o["start"],
                "tone_bearing_duration": duration,
                "previous_tone": o["preceding"]["label"] if o["preceding"] else None,
                "next_tone": o["following"]["label"] if o["following"] else None,
                "baseline_prediction": baseline[i],
                "categories": categories,
                "alignment_flag": row["spans"]["flags"],
                "transcript": o["transcript"],
            }
        )
    results = {
        "evaluated_at": now(),
        "selected_sha256": file_hash(folder / "selected.json"),
        "best_family_by_validation": best,
        "metrics": scores,
        "per_speaker": per_speaker,
        "predictions": predictions,
        "best_model_errors": errors,
    }
    write_json(folder / "test-results.json", results)
    write_json(
        folder / "test-seal.json",
        {
            "frozen_at": now(),
            "files": {
                name: file_hash(folder / name)
                for name in (
                    "selected.json",
                    "validation-trials.json",
                    "protocol.json",
                    "test-results.json",
                )
            },
            "external_probe_started": False,
        },
    )
    print("TEST RESULTS FROZEN", flush=True)
    return results


def run(release_folder, folder):
    release = verify_release(release_folder)
    verify_baseline()
    rows = read_rows(release_folder / "primary.jsonl")
    assert all(label_mutation_check(r) for r in rows)
    config = read_json(PACKAGE / "configs/aishell3-training.json")
    folder.mkdir(parents=True, exist_ok=True)
    sources = [
        Path(__file__),
        PACKAGE / "scripts/aishell3_acoustics.py",
        PACKAGE / "aishell3_acoustic_baseline.cjs",
        PACKAGE / "perceptual_tone/aishell3_learning.py",
        PACKAGE / "perceptual_tone/aishell3_embeddings.py",
        PACKAGE / "perceptual_tone/embeddings.py",
    ]
    protocol = {
        "release_sha256": file_hash(release_folder / "release.json"),
        "manifest_sha256": release["manifest_sha256"],
        "primary_sha256": file_hash(release_folder / "primary.jsonl"),
        "config": config,
        "runtime": runtime(),
        "source_hashes": {str(p.relative_to(PACKAGE)): file_hash(p) for p in sources},
        "leakage_mutation_checks": len(rows),
        "input_contract": "audio and numeric acoustics only; fixed released spans; no text",
        "preprocessing": "train-only median imputer and standardizer",
        "MLP_weighting": "balanced train sample weights",
        "baseline_input": (
            "original whole read unit, unchanged full-utterance Praat/graph/family functions"
        ),
        "label_limitation": (
            "corpus numbered tone, not independent perceived-tone annotation; "
            "forced alignment uses corpus transcript"
        ),
    }
    if (folder / "protocol.json").exists():
        if read_json(folder / "protocol.json") != protocol:
            raise ValueError("protocol_changed_start_new_run")
    else:
        write_json(folder / "protocol.json", protocol)
    values = acoustics(rows, folder)
    acoustic = {r["example_id"]: r for r in values}
    if set(acoustic) != {r["example_id"] for r in rows}:
        raise ValueError("acoustic_id_mismatch")
    names = acoustic_vector(values[0])[0]
    for row in values:
        changed = copy.deepcopy(row)
        changed.update(label="T9", expected_tone="T9", hanzi="泄漏", corpus_pinyin="x9")
        a, x = acoustic_vector(row)
        b, y = acoustic_vector(changed)
        assert names == a == b
        np.testing.assert_equal(x, y)
    schema = folder / "acoustic-feature-schema.json"
    if not schema.exists():
        write_json(schema, names)
    selected = select(rows, acoustic, folder, config)
    results = test(rows, acoustic, folder, selected)
    verify_release(release_folder)
    verify_baseline()
    print(
        json.dumps(
            {
                k: {m: v[m] for m in ("coverage", "accuracy", "balanced_accuracy", "macro_f1")}
                for k, v in results["metrics"].items()
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    args = parser.parse_args()
    run(args.release, args.run)

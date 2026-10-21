"""Inference-only learner transfer, gated on an immutable attested release."""

import subprocess
import tempfile
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import joblib
import numpy as np
from threadpoolctl import threadpool_limits

from .aishell3_embeddings import LAYERS, Encoder
from .aishell3_learning import validate_audio_contract
from .common import PACKAGE, ROOT, file_hash, read_json, read_rows, runtime, write_json, write_rows
from .learner_release import RELEASE, RUN, now, verify_release
from .manifest import verify_baseline

CLASSES = ("T1", "T2", "T3", "T4")


def contract(unit, whole=False):
    spans = unit["spans"]
    result = {
        "audio_reference": unit["audio"]["reference"],
        "audio_sha256": unit["audio"]["sha256"],
        "read_unit": [unit["start"], unit["end"]],
        "pooling": [
            spans["playback_read_unit" if whole else "tone_bearing_pooling_span"][k]
            for k in ("start_seconds", "end_seconds")
        ],
        "context": [spans["context"][k] for k in ("start_seconds", "end_seconds")],
    }
    validate_audio_contract(result)
    return result


def load_models(config):
    models = {}
    for name, spec in config["models"].items():
        if file_hash(spec["path"]) != spec["sha256"]:
            raise ValueError("model_hash_changed")
        model = joblib.load(spec["path"])
        lr = model.steps[-1][1]
        if tuple(model.classes_) != CLASSES or lr.C != 0.1 or lr.class_weight != "balanced":
            raise ValueError("frozen_model_configuration_mismatch")
        models[name] = model
    return models


def probabilities(models, matrix):
    with threadpool_limits(limits=4):
        result = {name: model.predict_proba(matrix) for name, model in models.items()}
    for values in result.values():
        if (
            values.shape != (len(matrix), 4)
            or not np.isfinite(values).all()
            or np.any(values < 0)
            or not np.allclose(values.sum(1), 1)
        ):
            raise ValueError("invalid_frozen_probabilities")
    return result


def deterministic(units, folder):
    """Use unchanged research bridges to the frozen production acoustic functions."""
    folder.mkdir(parents=True, exist_ok=False)
    groups = defaultdict(list)
    for u in units:
        groups[u["source_id"]].append(u)
    spec = [
        {
            "audio_path": rows[0]["audio"]["reference"],
            "audio_sha256": rows[0]["audio"]["sha256"],
            "units": [
                {"example_id": r["example_id"], "start": r["start"], "end": r["end"]} for r in rows
            ],
        }
        for rows in groups.values()
    ]
    write_json(folder / "input.json", spec)
    subprocess.run(
        [
            str(ROOT / "services/api/.venv/bin/python"),
            str(PACKAGE / "scripts/aishell3_acoustics.py"),
            str(folder / "input.json"),
            str(folder / "raw.json"),
        ],
        check=True,
    )
    subprocess.run(
        [
            "node",
            str(PACKAGE / "aishell3_acoustic_baseline.cjs"),
            str(folder / "raw.json"),
            str(folder / "output.json"),
        ],
        check=True,
    )
    return {r["example_id"]: r for r in read_json(folder / "output.json")}


def summary(rows):
    """Descriptive agreement only; never treat intended labels as realized-tone gold."""
    result = {"interpretation": "DESCRIPTIVE", "n": len(rows), "models": {}, "model_agreement": {}}
    names = ("expanded", "pilot", "deterministic")
    for name in names:
        covered = [r for r in rows if r[name]["prediction"] is not None]
        model = {"covered": len(covered), "abstentions": len(rows) - len(covered)}
        for label in ("intended_lexical_tone", "expected_surface_tone"):
            resolved = [r for r in rows if r[label] in (1, 2, 3, 4)]
            scored = [r for r in resolved if r[name]["prediction"] is not None]
            matches = sum(r[name]["prediction"] == f"T{r[label]}" for r in scored)
            model[label + "_agreement"] = {
                "matches": matches,
                "resolved_numbered_n": len(resolved),
                "covered_n": len(scored),
                "abstentions": len(resolved) - len(scored),
                "agreement_on_covered": matches / len(scored) if scored else None,
                "matching_fraction_all_resolved": matches / len(resolved) if resolved else None,
                "neutral_excluded": sum(r[label] == 5 for r in rows),
                "unresolved_excluded": sum(r[label] is None for r in rows),
            }
        model["prediction_counts"] = dict(Counter(r[name]["prediction"] or "ABSTAIN" for r in rows))
        if name != "deterministic":
            values = np.asarray([r[name]["confidence"] for r in rows])
            model["confidence"] = {
                "min": float(values.min()),
                "median": float(np.median(values)),
                "mean": float(values.mean()),
                "max": float(values.max()),
                "bins": {
                    f"{lo:g}-{hi:g}": int(
                        ((values >= lo) & (values < hi if hi < 1 else values <= hi)).sum()
                    )
                    for lo, hi in ((0.25, 0.5), (0.5, 0.8), (0.8, 0.9), (0.9, 1))
                },
                "expected_numbered_disagreements_at_least_0_8": sum(
                    r["expected_surface_tone"] in (1, 2, 3, 4)
                    and r[name]["prediction"] != f"T{r['expected_surface_tone']}"
                    and r[name]["confidence"] >= 0.8
                    for r in rows
                ),
                "not_calibrated_on_learner_speech": True,
            }
        result["models"][name] = model
    for a, b in combinations(names, 2):
        both = [
            r for r in rows if r[a]["prediction"] is not None and r[b]["prediction"] is not None
        ]
        matches = sum(r[a]["prediction"] == r[b]["prediction"] for r in both)
        result["model_agreement"][a + "_vs_" + b] = {
            "matches": matches,
            "jointly_covered": len(both),
            "fraction": matches / len(both) if both else None,
        }
    return result


def check_phase(phase):
    folder = RUN / phase
    seal = read_json(folder / "results-seal.json")
    if seal["release_manifest_sha256"] != verify_release()["manifest_sha256"]:
        raise ValueError("wrong_release")
    for name, sha in seal["files"].items():
        if file_hash(folder / name) != sha:
            raise ValueError("frozen_result_changed:" + name)
    return seal


def infer(phase):
    release_seal = verify_release()
    verify_baseline()
    if phase not in ("primary", "diagnostic", "unknown"):
        raise ValueError("unknown_phase")
    if phase != "primary":
        check_phase("primary")
    folder = RUN / phase
    if folder.exists():
        raise ValueError("inference_phase_exists_use_reproduce")
    folder.mkdir(parents=True)
    config = read_json(RELEASE / "inference-config.json")
    units = sorted(
        read_rows(RELEASE / (phase + ".jsonl")), key=lambda u: (u["source_id"], u["index"])
    )
    if any(
        u["quarantined"] or not u["eligible_for_evaluation"] or u["eligible_for_training"]
        for u in units
    ):
        raise ValueError("ineligible_unit")
    write_json(
        folder / "protocol.json",
        {
            "started_at": now(),
            "release_manifest_sha256": release_seal["manifest_sha256"],
            "phase": phase,
            "config": config,
            "runtime": runtime(),
            "script_sha256": file_hash(Path(__file__)),
            "learner_training_calls": 0,
            "label_input": False,
            "model_reselection": False,
            "primary_result_seal_sha256": file_hash(RUN / "primary/results-seal.json")
            if phase != "primary"
            else None,
        },
    )
    encoder = Encoder("chinese_hubert_base", folder / "embedding-cache", folder / "canonical")
    models = load_models(config)
    values, records = [], []
    for u in units:
        vectors, record = encoder.extract(contract(u), "context")
        values.append(vectors[LAYERS.index(9)])
        records.append(record)
    matrix = np.stack(values)
    with (folder / "features.npy").open("xb") as stream:
        np.save(stream, matrix, allow_pickle=False)
    probs = probabilities(models, matrix)
    baseline = deterministic(units, folder / "deterministic")
    rows = []
    for i, u in enumerate(units):
        row = {
            k: u[k]
            for k in (
                "example_id",
                "qa_item_id",
                "source_id",
                "index",
                "hanzi",
                "intended_phrase",
                "transcript",
                "intended_lexical_tone",
                "expected_surface_tone",
                "surface_basis",
                "surface_alternatives",
                "provenance_category",
                "whole_duration_seconds",
                "tone_duration_seconds",
            )
        }
        row.update(
            pinyin=u["alignment_pinyin"][:-1],
            realized_tone="UNKNOWN",
            audio_contract=contract(u),
            embedding=records[i],
        )
        for name, values in probs.items():
            row[name] = {
                "probabilities": values[i].tolist(),
                "prediction": CLASSES[values[i].argmax()],
                "confidence": float(values[i].max()),
            }
        row["deterministic"] = baseline[u["example_id"]]
        rows.append(row)
    write_rows(folder / "predictions.jsonl", rows)
    takes = {}
    quarantines = read_rows(RELEASE / (phase + "-quarantine.jsonl"))
    for ident in sorted({r["source_id"] for r in rows}):
        take = [r for r in rows if r["source_id"] == ident]
        takes[ident] = {
            **summary(take),
            "quarantined": sum(u["source_id"] == ident for u in quarantines),
            "phrase": take[0]["intended_phrase"] or take[0]["transcript"],
            "sequences": {
                name: [r[name]["prediction"] for r in take]
                for name in models | {"deterministic": None}
            },
        }
    write_json(folder / "summary.json", {**summary(rows), "takes": takes})
    files = {
        str(p.relative_to(folder)): file_hash(p) for p in sorted(folder.rglob("*")) if p.is_file()
    }
    write_json(
        folder / "results-seal.json",
        {
            "release_manifest_sha256": release_seal["manifest_sha256"],
            "frozen_at": now(),
            "files": files,
        },
    )
    check_phase(phase)
    return read_json(folder / "summary.json")


def reproduce(phase):
    check_phase(phase)
    folder = RUN / phase
    rows = read_rows(folder / "predictions.jsonl")
    matrix = np.load(folder / "features.npy", allow_pickle=False)
    actual = probabilities(load_models(read_json(RELEASE / "inference-config.json")), matrix)
    deltas = {}
    for name, values in actual.items():
        saved = np.asarray([r[name]["probabilities"] for r in rows])
        np.testing.assert_allclose(values, saved, atol=1e-12, rtol=0)
        deltas[name] = float(np.max(np.abs(values - saved)))
    # Fresh encoder reload, without embedding-cache reuse, one accepted unit per take.
    fresh_deltas, selected = {}, {}
    for i, row in enumerate(rows):
        selected.setdefault(row["source_id"], i)
    with tempfile.TemporaryDirectory(prefix="learner-reproduce-", dir=RUN) as tmp:
        encoder = Encoder("chinese_hubert_base", Path(tmp) / "cache", Path(tmp) / "canonical")
        for ident, i in selected.items():
            vectors, _ = encoder.extract(rows[i]["audio_contract"], "context")
            vector = vectors[LAYERS.index(9)]
            np.testing.assert_allclose(vector, matrix[i], atol=1e-6, rtol=0)
            fresh_deltas[ident] = float(np.max(np.abs(vector - matrix[i])))
        output = deterministic(read_rows(RELEASE / (phase + ".jsonl")), Path(tmp) / "deterministic")
        for row in rows:
            if output[row["example_id"]] != row["deterministic"]:
                raise ValueError("deterministic_reproduction_mismatch")
    result = {
        "phase": phase,
        "rows_reloaded": len(rows),
        "probability_max_deltas": deltas,
        "fresh_encoder_max_deltas_one_per_take": fresh_deltas,
        "deterministic_full_reproduction_exact": True,
        "no_refit": True,
    }
    write_json(RUN / (phase + "-reproduction.json"), result)
    return result


def representation_comparison():
    """Exploratory, after primary seal; same frozen models and context, no tuning."""
    for phase in ("primary", "diagnostic", "unknown"):
        check_phase(phase)
    folder = RUN / "representation-comparison"
    folder.mkdir(exist_ok=False)
    units = [
        u
        for phase in ("primary", "diagnostic", "unknown")
        for u in read_rows(RELEASE / (phase + ".jsonl"))
    ]
    predictions = {
        r["example_id"]: r
        for phase in ("primary", "diagnostic", "unknown")
        for r in read_rows(RUN / phase / "predictions.jsonl")
    }
    prior_path = PACKAGE / "models/generated/aishell3-first-four-tone-v1/external-probe.json"
    prior_seal = read_json(prior_path.with_name("external-probe-seal.json"))
    if file_hash(prior_path) != prior_seal["sha256"]:
        raise ValueError("historical_external_probe_changed")
    prior = read_json(prior_path)
    master = read_rows(RELEASE / "selected-take-provenance.jsonl")
    aliases = {}
    for take in master:
        for name in take["names"] + [Path(s["path"]).stem for s in take["sources"]]:
            aliases[name] = take["source_id"]
    old = {}
    for r in prior["predictions"]:
        source = aliases.get(r["recording"])
        if source:
            old[(source, r["index"], r["syllable"])] = r
    encoder = Encoder("chinese_hubert_base", folder / "embedding-cache", folder / "canonical")
    vectors = [
        encoder.extract(contract(u, whole=True), "context")[0][LAYERS.index(9)] for u in units
    ]
    matrix = np.stack(vectors)
    values = probabilities(load_models(read_json(RELEASE / "inference-config.json")), matrix)
    with (folder / "features.npy").open("xb") as stream:
        np.save(stream, matrix, allow_pickle=False)
    result = []
    for i, u in enumerate(units):
        before = old.get((u["source_id"], u["index"], u["hanzi"]))
        result.append(
            {
                "example_id": u["example_id"],
                "source_id": u["source_id"],
                "hanzi": u["hanzi"],
                "whole_qa_pass": u["qa"]["whole"] == "PASS",
                "controlled_whole_pooling_contract": contract(u, whole=True),
                "nucleus_coda": {name: predictions[u["example_id"]][name] for name in values},
                "controlled_whole": {
                    name: {
                        "probabilities": p[i].tolist(),
                        "prediction": CLASSES[p[i].argmax()],
                        "confidence": float(p[i].max()),
                    }
                    for name, p in values.items()
                },
                "prior_external_whole": before,
                "prior_comparison_caveat": (
                    "Prior segmentation/context differ; observed changes cannot be "
                    "attributed solely to pooling."
                ),
            }
        )
    write_rows(folder / "predictions.jsonl", result)
    write_json(
        folder / "seal.json",
        {
            "primary_result_seal_sha256": file_hash(RUN / "primary/results-seal.json"),
            "prior_probe_sha256": file_hash(prior_path),
            "files": {
                str(p.relative_to(folder)): file_hash(p)
                for p in sorted(folder.rglob("*"))
                if p.is_file()
            },
        },
    )
    return {
        "controlled_units": len(result),
        "matched_prior_units": sum(r["prior_external_whole"] is not None for r in result),
    }

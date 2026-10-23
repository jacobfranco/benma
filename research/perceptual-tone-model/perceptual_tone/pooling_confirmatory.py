"""Additive confirmatory replay: fixed recipes, write-once seal, then frozen heads."""

import argparse
import csv
import hashlib
import subprocess
from collections import Counter
from pathlib import Path

import numpy as np

from .aishell3_learning import audio_contract
from .common import PACKAGE, ROOT, file_hash, read_json, read_rows, runtime, write_json
from .frame_attribution import geometry
from .pooling_experiment import LOCK, OWNER, now, verify_files
from .pooling_representation import (
    acoustic_features,
    acoustic_weights,
    map_acoustics,
    representation,
)

OUT = PACKAGE / "data/generated/pooling-confirmatory-v1"
PRIOR = PACKAGE / "data/generated/pooling-representation-v1"
LEARNER = PACKAGE / "data/generated/releases/benma-learner-natural-v1-20261019"
ARMS = ("UNIFORM_SAFE_OWNER", "ACOUSTIC_WEIGHTED")
STATES = ("BASE", "CONTRACT_LEFT", "CONTRACT_RIGHT")
REFERENCE = "CURRENT_REFERENCE"


def remaining_native(rows, excluded):
    eligible = {
        r["example_id"]: r
        for r in rows
        if r["original"]["partition"] == "test" and r["primary_eligible"]
    }
    assert len(eligible) == 915 and len(excluded) == len(set(excluded)) == 256
    assert set(excluded) <= eligible.keys()
    result = [eligible[i] for i in sorted(eligible.keys() - set(excluded))]
    assert len(result) == 659
    return result


def variant(arm, state, ownership, owner_span, ids, centers, features):
    """Geometry and acoustic inputs only; delegate unchanged pooling to sealed code."""
    if arm not in ARMS or state not in STATES:
        raise ValueError("unknown_confirmatory_condition")
    ids = np.asarray(ids, int)
    selected = (
        ids
        if state == "BASE" or ownership != "safe"
        else (ids[1:] if state == "CONTRACT_LEFT" else ids[:-1])
    )
    row = representation(arm, ownership, owner_span, selected, centers, features)
    row.update(
        perturbation=state,
        eligible_frame_ids=ids.tolist(),
        eligible_frame_centers=centers[ids].tolist(),
        frame_count=len(selected),
    )
    row["perturbation_status"] = "base" if state == "BASE" else "admissible"
    if ownership != "safe":
        row["perturbation_status"] = "ownership_abstained"
    elif state != "BASE" and (len(selected) < 3 or row["support_ms"] < 60 - 1e-6):
        row["perturbation_status"] = "perturbation_not_admissible"
        row["abstention_reason"] = "perturbation_not_admissible"
    # Save acoustic audit fields for both arms, without using them for uniform pooling.
    mapped = map_acoustics(centers[selected], features) if len(selected) else []
    raw = acoustic_weights(
        [r["rms_20ms"] for r in mapped], [r["high_band_fraction"] for r in mapped]
    )
    total = float(raw.sum())
    row["acoustic_audit"] = {
        "rms_20ms": [r["rms_20ms"] for r in mapped],
        "high_band_fraction": [r["high_band_fraction"] for r in mapped],
        "raw_weights": raw.tolist(),
        "normalized_weights": (raw / total).tolist() if total > np.finfo(float).tiny else [],
        "mapped_timestamps": [r["time"] for r in mapped],
    }
    return row


def pcm_hash(path):
    from .aishell3_embeddings import decode

    pcm, rate, _ = decode(path)
    return {"rate": rate, "samples": len(pcm), "sha256": hashlib.sha256(pcm.tobytes()).hexdigest()}


def preregister():
    from .learner_transfer import contract as learner_contract
    from .pooling_experiment import verify_manifest as verify_prior

    verify_prior()
    lock = read_json(LOCK)
    native_path = ROOT / lock["native_release"] / "manifest.jsonl"
    all_native = read_rows(native_path)
    excluded = read_json(PRIOR / "native-control-ids.json")["ids"]
    native = remaining_native(all_native, excluded)
    pilot_path = (
        PACKAGE
        / "data/generated/aishell3/releases/aishell3-nucleus-coda-context-v1-20261017"
        / "manifest.jsonl"
    )
    train_speakers = {
        r["original"]["speaker_id"]
        for r in all_native + read_rows(pilot_path)
        if r["original"]["partition"] == "train"
    }
    speakers = sorted({r["original"]["speaker_id"] for r in native})
    assert not set(speakers) & train_speakers
    old_plan = read_json(PRIOR / "preregistration.json")
    old_meta = read_json(PRIOR / "evaluation-metadata.json")
    items = [
        {**i, "cached_hidden": str(PRIOR / f"representations/{n:04}-layer9.npy")}
        for n, i in enumerate(old_plan["items"])
        if i["dataset"] == "physical"
    ]
    meta = {
        i["id"]: {
            **old_meta[i["id"]],
            "speaker": "playback_google" if i["id"].startswith("google") else "jacob",
        }
        for i in items
    }
    physical_pcm = {
        i["contract"]["audio_reference"]: pcm_hash(i["contract"]["audio_reference"]) for i in items
    }
    learner_audit = []
    # Include all accepted natural and documented diagnostic units; retain quarantine.
    for stratum in ("primary", "diagnostic"):
        for u in read_rows(LEARNER / f"{stratum}.jsonl"):
            assert not u["quarantined"] and u["eligible_for_evaluation"]
            identity = pcm_hash(u["audio"]["reference"])
            overlaps = [p for p, h in physical_pcm.items() if h == identity]
            learner_audit.append(
                {
                    "id": u["example_id"],
                    "source_id": u["source_id"],
                    "stratum": stratum,
                    "pcm": identity,
                    "overlap": overlaps,
                    "original_sources": u["original_sources"],
                }
            )
            if overlaps:
                continue
            ref = learner_contract(u)
            items.append(
                {
                    "id": u["example_id"],
                    "dataset": "learner_" + stratum,
                    "contract": {**ref, "pooling": ref["read_unit"]},
                    "reference_contract": ref,
                    "reference_usable": True,
                    "ownership": "safe",
                    "owner_usable": True,
                    "ownership_source": "frozen_accepted_learner_MFA_read_unit",
                }
            )
            meta[u["example_id"]] = {
                "speaker": u["alignment_speaker_group"],
                "source_id": u["source_id"],
                "native_label": None,
                "head_compatible": u["corpus_tone"] != 5,
                "display": u["example_id"],
            }
    for r in native:
        ref = audio_contract(r)
        items.append(
            {
                "id": r["example_id"],
                "dataset": "native",
                "contract": {**ref, "pooling": ref["read_unit"]},
                "reference_contract": ref,
                "reference_usable": True,
                "ownership": "safe",
                "owner_usable": True,
                "ownership_source": "frozen_native_MFA_read_unit",
            }
        )
        meta[r["example_id"]] = {
            "speaker": r["original"]["speaker_id"],
            "native_label": r["original"]["label"],
            "head_compatible": True,
            "display": r["example_id"],
        }
    paths = {Path(p) for p in read_json(PRIOR / "freeze-before.json")["files"]}
    paths.update(p for p in PRIOR.rglob("*") if p.is_file())
    paths.update(Path(i["contract"]["audio_reference"]) for i in items)
    paths.update([Path(__file__), PACKAGE / "perceptual_tone/pooling_confirmatory_analysis.py"])
    write_json(
        OUT / "freeze-before.json",
        {
            "created_at": now(),
            "files": {str(p): file_hash(p) for p in sorted(paths)},
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT)
            .decode()
            .strip(),
            "git_status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT).decode(),
        },
    )
    write_json(
        OUT / "native-ids.json", {"ids": [r["example_id"] for r in native], "speakers": speakers}
    )
    write_json(
        OUT / "prior-256-exclusion-proof.json",
        {
            "eligible_count": 915,
            "prior_count": 256,
            "confirmatory_count": 659,
            "intersection": [],
            "excluded_ids": excluded,
            "union_equals_eligible": True,
            "training_speaker_intersection": [],
            "selection": (
                "All eligible test IDs minus exact prior sealed IDs, "
                "lexicographic order; no resampling"
            ),
            "prior_ids_sha256": file_hash(PRIOR / "native-control-ids.json"),
            "release_sha256": file_hash(native_path),
        },
    )
    write_json(
        OUT / "disjoint-learner-ids.json",
        {
            "audit": learner_audit,
            "physical_pcm": physical_pcm,
            "ids": [i["id"] for i in items if i["dataset"].startswith("learner")],
            "policy": (
                "All frozen accepted primary/diagnostic units with disjoint "
                "source PCM; unknown-provenance and quarantined material not "
                "promoted. No realized-tone gold; stability only."
            ),
        },
    )
    write_json(OUT / "evaluation-metadata.json", meta)
    write_json(
        OUT / "preregistration.json",
        {
            "created_at": now(),
            "arms": ARMS,
            "perturbations": STATES,
            "items": items,
            "formula": read_json(PRIOR / "preregistration.json")["acoustic"],
            "unchanged_rules": {
                k: read_json(PRIOR / "preregistration.json")[k]
                for k in ("features", "mapping", "normalization", "support", "encoder")
            },
            "perturbation_rule": (
                "BASE unchanged; remove exactly one eligible frame at "
                "left/right; same owner boundaries; >=3 frames and >=60ms "
                "clipped frame-cell support, else "
                "perturbation_not_admissible. Ownership abstention persists."
            ),
            "reference": (
                "Exact frozen native test layer9 archive; physical and "
                "learner frozen nucleus-coda span, same encoder context. "
                "Comparator only, no perturbations."
            ),
            "metadata_policy": (
                "Native labels evaluation only. No learner accuracy. "
                "Pre-existing neutral class compatibility applied only after "
                "vectors sealed."
            ),
            "analysis": (
                "All available and pairwise common coverage; "
                "accuracy/balanced accuracy/F1/recalls/confusion. BASE vs "
                "left/right TV, flips, margins, cosine/L2; per-tone and both "
                "heads. Arm differences on same pairs; descriptive edge "
                "acoustic correlations. Distribution against each frozen "
                "scaler. Effective-n descriptive only."
            ),
            "uncertainty": (
                "Paired native correctness difference: 10000 speaker-cluster "
                "bootstrap replicates, seed 20261022, 95% percentile "
                "interval. Report paired wins/losses, no threshold or "
                "significance search; few held-out speakers limit inference."
            ),
            "decision": (
                "User's four qualitative categories; no post-hoc numerical "
                "materiality threshold, no equivalence claim from point "
                "estimates. A requires all stated criteria; mixed stability "
                "with preserved native recognition -> PROMISING_NOT_READY."
            ),
            "code_hashes": {
                str(p): file_hash(p)
                for p in [
                    Path(__file__),
                    PACKAGE / "perceptual_tone/pooling_representation.py",
                    PACKAGE / "perceptual_tone/pooling_confirmatory_analysis.py",
                ]
            },
            "artifacts": {
                name: file_hash(OUT / name)
                for name in [
                    "native-ids.json",
                    "prior-256-exclusion-proof.json",
                    "disjoint-learner-ids.json",
                    "evaluation-metadata.json",
                    "freeze-before.json",
                ]
            },
            "runtime": runtime(),
        },
    )
    write_json(
        OUT / "preregistration-seal.json",
        {
            "sha256": file_hash(OUT / "preregistration.json"),
            "sealed_at": now(),
            "classifier_loaded": False,
        },
    )
    print("PREREGISTERED", Counter(i["dataset"] for i in items), flush=True)


def verify_plan():
    assert (
        file_hash(OUT / "preregistration.json")
        == read_json(OUT / "preregistration-seal.json")["sha256"]
    )
    plan = read_json(OUT / "preregistration.json")
    verify_files(plan["code_hashes"])
    verify_files({str(OUT / p): h for p, h in plan["artifacts"].items()})
    verify_files(read_json(OUT / "freeze-before.json")["files"])
    return plan


def construct():
    import torch

    from .aishell3_embeddings import Encoder, canonical_audio, input_audio
    from .ownership_diagnostics import audio

    plan = verify_plan()
    meta = read_json(OUT / "evaluation-metadata.json")
    encoder = Encoder("chinese_hubert_base", OUT / "cache/unused", OUT / "cache/canonical")
    assert encoder.base.weights == read_json(LOCK)["encoder_weights"]
    archive = (
        PACKAGE / "models/generated/aishell3-multispeaker-fixed-v2/test-chinese_hubert_base-context"
    )
    archive_index = read_json(archive.with_suffix(".json"))
    assert file_hash(archive.with_suffix(".npz")) == archive_index["sha256"]
    references = dict(
        zip(archive_index["ids"], np.load(archive.with_suffix(".npz"))["values"][:, 1], strict=True)
    )
    records, files, cache, errors = [], {}, {}, []
    (OUT / "representations").mkdir(exist_ok=True)
    for number, item in enumerate(plan["items"]):
        contract = item["contract"]
        centers, ids = geometry(contract)
        key = contract["audio_sha256"]
        if key not in cache:
            if item["dataset"] == "physical":
                recording = item["id"].rsplit("-", 1)[0]
                with (OWNER / f"diagnostics/{recording}-features.csv").open() as f:
                    cache[key] = [
                        {k: float(r[k]) for k in ("time", "rms_20ms", "high_band_fraction")}
                        for r in csv.DictReader(f)
                    ]
            else:
                path = canonical_audio(contract["audio_reference"], key, OUT / "cache/canonical")
                values, rate = audio(path)
                cache[key] = acoustic_features(values, rate)
        rows = [
            variant(a, s, item["ownership"], contract["pooling"], ids, centers, cache[key])
            for a in ARMS
            for s in STATES
        ]
        if not item["owner_usable"]:
            for row in rows:
                row["abstention_reason"] = row["abstention_reason"] or item["ownership_reason"]
        hidden_path = Path(
            item.get("cached_hidden", OUT / f"representations/{number:04}-layer9.npy")
        )
        if hidden_path.exists():
            hidden = np.load(hidden_path, allow_pickle=False)
        else:
            values, _, _ = input_audio(contract, "context", OUT / "cache/canonical")
            if encoder.base.model is None:
                encoder.base._load()
            inputs = encoder.base.processor(values, sampling_rate=16000, return_tensors="pt")
            with torch.inference_mode():
                hidden = (
                    encoder.base.model(**inputs, output_hidden_states=True)
                    .hidden_states[9][0]
                    .cpu()
                    .numpy()
                    .copy()
                )
            with hidden_path.open("xb") as f:
                np.save(f, hidden, allow_pickle=False)
        assert hidden.shape == (len(centers), 768) and np.isfinite(hidden).all()
        files[str(hidden_path)] = file_hash(hidden_path)
        for row in rows:
            row.update(
                id=item["id"],
                dataset=item["dataset"],
                speaker=meta[item["id"]]["speaker"],
                native_label=meta[item["id"]]["native_label"],
                hidden_path=str(hidden_path),
                pooled_vector=None,
                ownership_source=item["ownership_source"],
            )
            if row["abstention_reason"] is None:
                row["pooled_vector"] = (
                    np.array(row["normalized_weights"]) @ hidden[row["frame_ids"]].astype(float)
                ).tolist()
            records.append(row)
        if item["reference_usable"]:
            ref_centers, ref_ids = geometry(item["reference_contract"])
            np.testing.assert_array_equal(ref_centers, centers)
            vector = hidden[ref_ids].astype(float).mean(0)
            if item["dataset"] == "native":
                errors.append(float(np.max(np.abs(vector - references[item["id"]]))))
                assert errors[-1] < 1e-6
                vector = references[item["id"]].astype(float)
            records.append(
                {
                    "id": item["id"],
                    "dataset": item["dataset"],
                    "arm": REFERENCE,
                    "perturbation": "BASE",
                    "frame_ids": ref_ids.tolist(),
                    "frame_centers": centers[ref_ids].tolist(),
                    "ownership_span": item["reference_contract"]["pooling"],
                    "pooled_vector": vector.tolist(),
                    "abstention_reason": None,
                    "speaker": meta[item["id"]]["speaker"],
                    "native_label": meta[item["id"]]["native_label"],
                }
            )
        if number % 20 == 0:
            print(
                f"constructed {number + 1}/{len(plan['items'])}; classifier not loaded", flush=True
            )
    write_json(
        OUT / "representation-manifest.json",
        {
            "records": records,
            "files": files,
            "preregistration_sha256": file_hash(OUT / "preregistration.json"),
            "encoder_weights": encoder.base.weights,
            "native_reference_max_reextraction_error": max(errors),
            "native_reference_archive_sha256": archive_index["sha256"],
        },
    )
    write_json(
        OUT / "representation-manifest-seal.json",
        {
            "sha256": file_hash(OUT / "representation-manifest.json"),
            "sealed_at": now(),
            "classifier_loaded": False,
            "row_count": len(records),
            "usable_counts": dict(
                Counter(
                    f"{r['dataset']}/{r['arm']}/{r['perturbation']}"
                    for r in records
                    if r["pooled_vector"] is not None
                )
            ),
        },
    )
    print("SEALED", file_hash(OUT / "representation-manifest.json"), flush=True)


def verify_manifest():
    verify_plan()
    assert (
        file_hash(OUT / "representation-manifest.json")
        == read_json(OUT / "representation-manifest-seal.json")["sha256"]
    )
    manifest = read_json(OUT / "representation-manifest.json")
    assert manifest["preregistration_sha256"] == file_hash(OUT / "preregistration.json")
    verify_files(manifest["files"])
    return manifest


def infer():
    from .frame_attribution import affine_head
    from .learner_transfer import load_models

    manifest = verify_manifest()
    write_json(
        OUT / "inference-start.json",
        {
            "started_at": now(),
            "manifest_sha256": file_hash(OUT / "representation-manifest.json"),
            "seal_sha256": file_hash(OUT / "representation-manifest-seal.json"),
        },
    )
    models = load_models(read_json(LOCK)["model_method"])
    meta = read_json(OUT / "evaluation-metadata.json")
    refs = {
        r["id"]: np.array(r["pooled_vector"]) for r in manifest["records"] if r["arm"] == REFERENCE
    }
    results = []
    for r in manifest["records"]:
        if r["pooled_vector"] is None or not meta[r["id"]]["head_compatible"]:
            continue
        v = np.array(r["pooled_vector"])
        for name, model in models.items():
            mu, scale, coef, bias, _ = affine_head(model)
            logits = ((v - mu) / scale) @ coef.T + bias
            probs = model.predict_proba(v[None])[0]
            ref = refs.get(r["id"])
            results.append(
                {k: r[k] for k in ("id", "dataset", "arm", "perturbation")}
                | {
                    "head": name,
                    "prediction": str(model.classes_[probs.argmax()]),
                    "probabilities": probs.tolist(),
                    "logits": logits.tolist(),
                    "classes": model.classes_.tolist(),
                    "probability_margin": float(np.diff(np.sort(probs)[-2:])[0]),
                    "logit_margin": float(np.diff(np.sort(logits)[-2:])[0]),
                    "standardized_norm": float(np.linalg.norm((v - mu) / scale)),
                    "distance_to_training_mean": float(np.linalg.norm(v - mu)),
                    "cosine_to_reference": float(
                        v @ ref / (np.linalg.norm(v) * np.linalg.norm(ref))
                    )
                    if ref is not None
                    else None,
                    "l2_to_reference": float(np.linalg.norm(v - ref)) if ref is not None else None,
                    "standardized_distance_to_reference": float(np.linalg.norm((v - ref) / scale))
                    if ref is not None
                    else None,
                }
            )
    write_json(
        OUT / "predictions.json",
        {
            "completed_at": now(),
            "manifest_sha256": file_hash(OUT / "representation-manifest.json"),
            "rows": results,
        },
    )
    verify_manifest()
    write_json(
        OUT / "freeze-after.json",
        {
            "verified_at": now(),
            "changed": [],
            "verified_files": len(read_json(OUT / "freeze-before.json")["files"]),
            "git_head_unchanged": read_json(OUT / "freeze-before.json")["git_head"]
            == subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
            "manifest_sha256": file_hash(OUT / "representation-manifest.json"),
        },
    )
    print("INFERENCE COMPLETE", len(results), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("preregister", "construct", "infer", "verify"))
    {"preregister": preregister, "construct": construct, "infer": infer, "verify": verify_manifest}[
        parser.parse_args().phase
    ]()

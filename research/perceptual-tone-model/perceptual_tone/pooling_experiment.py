"""Write-once preregistration -> representations -> seal -> frozen inference."""

import argparse
import csv
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from .aishell3_learning import audio_contract
from .common import PACKAGE, ROOT, file_hash, read_json, read_rows, runtime, write_json
from .frame_attribution import geometry
from .pooling_representation import ARMS, acoustic_features, native_subset, representation

OUT = PACKAGE / "data/generated/pooling-representation-v1"
OWNER = PACKAGE / "data/generated/ownership-selector-v1"
LOCK = PACKAGE / "configs/dev-learned-lock.json"
CODE = [Path(__file__), PACKAGE / "perceptual_tone/pooling_representation.py"]


def now():
    return datetime.now(UTC).isoformat()


def verify_files(files):
    changed = [p for p, sha in files.items() if not Path(p).is_file() or file_hash(p) != sha]
    if changed:
        raise ValueError(f"sealed_files_changed: {changed}")


def preregister():
    lock = read_json(LOCK)
    release = ROOT / lock["native_release"]
    manifest = release / "manifest.jsonl"
    native = native_subset(read_rows(manifest))
    pilot_release = (
        PACKAGE / "data/generated/aishell3/releases/aishell3-nucleus-coda-context-v1-20261017"
    )
    pilot_rows = read_rows(pilot_release / "manifest.jsonl")
    pilot_train = {
        r["original"]["speaker_id"] for r in pilot_rows if r["original"]["partition"] == "train"
    }
    expanded_train = {
        r["original"]["speaker_id"]
        for r in read_rows(manifest)
        if r["original"]["partition"] == "train"
    }
    speakers = {r["original"]["speaker_id"] for r in native}
    assert not speakers & (pilot_train | expanded_train)
    items, labels = [], {}
    for r in read_json(OWNER / "results.json")["rows"]:
        if r["candidate"] != "GAP_AWARE_AZURE":
            continue
        identifier = f"{r['recording']}-{r['index']}"
        items.append(
            {
                "id": identifier,
                "dataset": "physical",
                "contract": r["contract"],
                "ownership": r["selection"]["ownership"],
                "ownership_reason": r["selection"]["reason"],
                "owner_usable": r["selection"]["representation"] == "usable",
                "ownership_source": "persisted_GAP_AWARE_AZURE",
                "reference_contract": r["current_reference"]["contract"],
                "reference_usable": r["current_reference"]["gate_reason"] is None,
            }
        )
        labels[identifier] = {
            "display": f"{r['recording']} {r['character']}",
            "head_compatible": not r["neutral"],
            "native_label": None,
        }
    for r in native:
        ref = audio_contract(r)
        contract = {**ref, "pooling": ref["read_unit"]}
        items.append(
            {
                "id": r["example_id"],
                "dataset": "native",
                "contract": contract,
                "ownership": "safe",
                "owner_usable": True,
                "ownership_reason": "frozen_native_MFA_read_unit",
                "ownership_source": "frozen_native_MFA_not_Azure",
                "reference_contract": ref,
                "reference_usable": True,
            }
        )
        labels[r["example_id"]] = {
            "display": r["example_id"],
            "head_compatible": True,
            "native_label": r["original"]["label"],
            "speaker": r["original"]["speaker_id"],
        }
    paths = {LOCK, manifest, pilot_release / "manifest.jsonl", *CODE}
    paths.update(ROOT / p for p in lock["files"])
    for folder in ("ownership-selector-v1", "frame-attribution-v1", "f0-independent-v1"):
        paths.update(p for p in (PACKAGE / "data/generated" / folder).rglob("*") if p.is_file())
    paths.update(PACKAGE.glob("perceptual_tone/*.py"))
    paths.update(PACKAGE.glob("models/generated/**/*.joblib"))
    for folder in (release, pilot_release, PACKAGE / "data/generated/releases"):
        paths.update(p for p in folder.rglob("*") if p.is_file())
    tracked = subprocess.check_output(["git", "ls-files", "services/api", "apps"], cwd=ROOT)
    paths.update(ROOT / p for p in tracked.decode().splitlines())
    paths.update(Path(i["contract"]["audio_reference"]) for i in items)
    write_json(
        OUT / "freeze-before.json",
        {
            "created_at": now(),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT)
            .decode()
            .strip(),
            "git_status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT).decode(),
            "files": {str(p): file_hash(p) for p in sorted(paths) if p.is_file()},
        },
    )
    write_json(
        OUT / "native-control-ids.json",
        {
            "selection": (
                "64 per T1/T2/T3/T4; round robin sorted speakers, lexicographic IDs within speaker"
            ),
            "ids": [r["example_id"] for r in native],
            "speakers": sorted(speakers),
            "speaker_disjoint_both_training_sets": True,
            "labels_for_stratification_and_evaluation_only": {
                r["example_id"]: r["original"]["label"] for r in native
            },
        },
    )
    write_json(OUT / "evaluation-metadata.json", labels)
    write_json(
        OUT / "preregistration.json",
        {
            "created_at": now(),
            "code_hashes": {str(p): file_hash(p) for p in CODE},
            "arms": list(ARMS),
            "uniform": "All eligible frame centers inside fixed owner, uniform float64 mean.",
            "central": (
                "K=ceil(N/2); start=floor((N-K)/2); K consecutive frames; tied "
                "center biased earlier."
            ),
            "acoustic": "RMS_20ms * (1-high_band_fraction); no exponents, floors, or search.",
            "features": (
                "Original diagnostics: uncentered RMS; demeaned 20ms symmetric "
                "Hann FFT; power >=3400Hz / max(total power,1e-24). 5ms hop, full"
                " waveform."
            ),
            "mapping": (
                "Nearest acoustic timestamp to absolute encoder center; earlier "
                "on tie; no interpolation. Physical saved CSV. Native canonical "
                "PCM16 16kHz with same equations."
            ),
            "normalization": (
                "Float64 weights/sum; clamp negative RMS to 0 and high fraction "
                "to [0,1] only; nonfinite rejected; total<=float64.tiny abstains,"
                " no fallback."
            ),
            "zero_weight_epsilon": float(np.finfo(np.float64).tiny),
            "support": (
                "At least 3 frames and >=60ms contiguous frame-cell span clipped "
                "to owner (1e-9 s arithmetic tolerance). No expansion. Kish "
                "1/sum(w^2), and Kish*20ms descriptive only; no new effective-n "
                "gate."
            ),
            "encoder": (
                "Pinned Chinese HuBERT layer9; existing context/PCM16/200sample "
                "padding/normalization/half-open centers; same context for every "
                "arm and reference; no fitting."
            ),
            "reference": (
                "Frozen current physical / native nucleus-coda pooling for "
                "comparison only, not a fourth candidate. Existing native "
                "reference may have <60ms; preserved as historical comparator."
            ),
            "ownership": (
                "Physical persisted GAP_AWARE_AZURE, never rerun. Native frozen "
                "MFA read-unit boundaries: no native Azure exists, so a "
                "representation-transfer control, not an Azure-selector "
                "validation."
            ),
            "neutral": (
                "Construct representations without tone inputs; skip four-class "
                "inference on four pre-existing neutral units using separate "
                "compatibility metadata."
            ),
            "analysis": (
                "Native metrics on available cases plus common-covered paired "
                "cases, accuracy/balanced accuracy/macro F1/recalls/confusion; no"
                " physical accuracy. TV, argmax, probability and logit margins, "
                "head disagreements, standardized norms, distances to scaler "
                "means, reference cosine. Previously identified frame groups "
                "assessed by pooled weight mass; no new attribution audit or "
                "ablation arms."
            ),
            "decision": (
                "No numerical readiness threshold fitted. Require convergent "
                "coverage/native/stability/head evidence; mixed evidence -> "
                "NO_CLEAR_WINNER. 256 clustered observations detect large "
                "regressions, not equivalence or clinical perceptual truth."
            ),
            "items": items,
            "native_ids_sha256": file_hash(OUT / "native-control-ids.json"),
            "metadata_sha256": file_hash(OUT / "evaluation-metadata.json"),
            "freeze_sha256": file_hash(OUT / "freeze-before.json"),
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
    print("PREREGISTERED", file_hash(OUT / "preregistration.json"), flush=True)


def verify_preregistration():
    seal = read_json(OUT / "preregistration-seal.json")
    assert seal["sha256"] == file_hash(OUT / "preregistration.json")
    plan = read_json(OUT / "preregistration.json")
    verify_files(plan["code_hashes"])
    for name, key in (
        ("native-control-ids.json", "native_ids_sha256"),
        ("evaluation-metadata.json", "metadata_sha256"),
        ("freeze-before.json", "freeze_sha256"),
    ):
        assert file_hash(OUT / name) == plan[key]
    return plan


def construct():
    import torch

    from .aishell3_embeddings import Encoder, canonical_audio, input_audio
    from .ownership_diagnostics import audio

    plan = verify_preregistration()
    verify_files(read_json(OUT / "freeze-before.json")["files"])
    encoder = Encoder("chinese_hubert_base", OUT / "cache/unused", OUT / "cache/canonical")
    assert encoder.base.weights == read_json(LOCK)["encoder_weights"]
    records, files, feature_cache = [], {}, {}
    (OUT / "representations").mkdir(exist_ok=True)
    for number, item in enumerate(plan["items"]):
        contract = item["contract"]
        centers, ids = geometry(contract)
        if item["dataset"] == "physical":
            recording = item["id"].rsplit("-", 1)[0]
            if recording not in feature_cache:
                with (OWNER / f"diagnostics/{recording}-features.csv").open() as f:
                    feature_cache[recording] = [
                        {k: float(r[k]) for k in ("time", "rms_20ms", "high_band_fraction")}
                        for r in csv.DictReader(f)
                    ]
            features = feature_cache[recording]
        else:
            key = contract["audio_sha256"]
            if key not in feature_cache:
                path = canonical_audio(contract["audio_reference"], key, OUT / "cache/canonical")
                values, rate = audio(path)
                feature_cache[key] = acoustic_features(values, rate)
            features = feature_cache[key]
        rows = [
            representation(arm, item["ownership"], contract["pooling"], ids, centers, features)
            for arm in ARMS
        ]
        if not item["owner_usable"]:
            for row in rows:
                row["abstention_reason"] = row["abstention_reason"] or item["ownership_reason"]
        hidden = None
        if any(r["abstention_reason"] is None for r in rows) or item["reference_usable"]:
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
            assert hidden.shape == (len(centers), 768) and np.isfinite(hidden).all()
            path = OUT / f"representations/{number:04}-layer9.npy"
            with path.open("xb") as f:
                np.save(f, hidden, allow_pickle=False)
            files[str(path)] = file_hash(path)
        for row in rows:
            row.update(id=item["id"], dataset=item["dataset"], vector_path=None)
            if row["abstention_reason"] is None:
                vector = np.array(row["normalized_weights"]) @ hidden[row["frame_ids"]].astype(
                    float
                )
                path = OUT / f"representations/{number:04}-{row['arm']}.npy"
                with path.open("xb") as f:
                    np.save(f, vector, allow_pickle=False)
                row["vector_path"] = str(path)
                files[str(path)] = file_hash(path)
            records.append(row)
        if item["reference_usable"]:
            ref_centers, ref_ids = geometry(item["reference_contract"])
            np.testing.assert_array_equal(ref_centers, centers)
            path = OUT / f"representations/{number:04}-CURRENT_REFERENCE.npy"
            with path.open("xb") as f:
                np.save(f, hidden[ref_ids].astype(float).mean(0), allow_pickle=False)
            files[str(path)] = file_hash(path)
            records.append(
                {
                    "id": item["id"],
                    "dataset": item["dataset"],
                    "arm": "CURRENT_REFERENCE",
                    "vector_path": str(path),
                    "frame_ids": ref_ids.tolist(),
                    "frame_centers": centers[ref_ids].tolist(),
                    "ownership_span": item["reference_contract"]["pooling"],
                    "abstention_reason": None,
                }
            )
        if number % 16 == 0:
            print(
                f"constructed {number + 1}/{len(plan['items'])}; no classifier loaded", flush=True
            )
    write_json(
        OUT / "representation-manifest.json",
        {
            "preregistration_sha256": file_hash(OUT / "preregistration.json"),
            "encoder_weights": encoder.base.weights,
            "records": records,
            "files": files,
        },
    )
    write_json(
        OUT / "representation-manifest-seal.json",
        {
            "sha256": file_hash(OUT / "representation-manifest.json"),
            "sealed_at": now(),
            "classifier_loaded": False,
            "representations_complete": True,
        },
    )
    print("SEALED", file_hash(OUT / "representation-manifest.json"), flush=True)


def verify_manifest():
    verify_preregistration()
    seal = read_json(OUT / "representation-manifest-seal.json")
    assert file_hash(OUT / "representation-manifest.json") == seal["sha256"]
    manifest = read_json(OUT / "representation-manifest.json")
    assert manifest["preregistration_sha256"] == file_hash(OUT / "preregistration.json")
    verify_files(manifest["files"])
    verify_files(read_json(OUT / "freeze-before.json")["files"])
    return manifest


def infer():
    from .frame_attribution import affine_head
    from .learner_transfer import load_models

    manifest = verify_manifest()
    # This write-once event is AFTER all vectors are sealed, BEFORE either joblib is loaded.
    write_json(
        OUT / "inference-start.json",
        {
            "started_at": now(),
            "manifest_sha256": file_hash(OUT / "representation-manifest.json"),
            "seal_sha256": file_hash(OUT / "representation-manifest-seal.json"),
        },
    )
    models = load_models(read_json(LOCK)["model_method"])
    metadata = read_json(OUT / "evaluation-metadata.json")
    references = {
        r["id"]: np.load(r["vector_path"], allow_pickle=False)
        for r in manifest["records"]
        if r["arm"] == "CURRENT_REFERENCE"
    }
    results = []
    for r in manifest["records"]:
        if r["vector_path"] is None or not metadata[r["id"]]["head_compatible"]:
            continue
        vector = np.load(r["vector_path"], allow_pickle=False)
        for name, model in models.items():
            mu, scale, coef, bias, _ = affine_head(model)
            standardized = (vector - mu) / scale
            logits = standardized @ coef.T + bias
            probs = model.predict_proba(vector[None])[0]
            reference = references.get(r["id"])
            results.append(
                {
                    "id": r["id"],
                    "dataset": r["dataset"],
                    "arm": r["arm"],
                    "head": name,
                    "prediction": str(model.classes_[probs.argmax()]),
                    "probabilities": probs.tolist(),
                    "logits": logits.tolist(),
                    "probability_margin": float(np.sort(probs)[-1] - np.sort(probs)[-2]),
                    "logit_margin": float(np.sort(logits)[-1] - np.sort(logits)[-2]),
                    "standardized_norm": float(np.linalg.norm(standardized)),
                    "distance_to_training_mean": float(np.linalg.norm(vector - mu)),
                    "cosine_to_reference": (
                        float(
                            np.dot(vector, reference)
                            / (np.linalg.norm(vector) * np.linalg.norm(reference))
                        )
                        if reference is not None
                        else None
                    ),
                    "standardized_distance_to_reference": (
                        float(np.linalg.norm((vector - reference) / scale))
                        if reference is not None
                        else None
                    ),
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
    phase = parser.parse_args().phase
    {"preregister": preregister, "construct": construct, "infer": infer, "verify": verify_manifest}[
        phase
    ]()

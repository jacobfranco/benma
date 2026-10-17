"""Reproduce the released experiment without changing any research result."""

import hashlib
import json
import sys
import tempfile
import warnings
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
from sklearn.utils.class_weight import compute_sample_weight
from threadpoolctl import threadpool_limits

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aishell3_release import SPEAKERS, verify_release
from aishell3_train import DEFAULT_RELEASE, DEFAULT_RUN, feature_matrix, probabilities
from perceptual_tone.aishell3_embeddings import LAYERS, Encoder, input_audio
from perceptual_tone.aishell3_learning import audio_contract, label_mutation_check, metric, pipeline
from perceptual_tone.common import PACKAGE, ROOT, file_hash, read_json, read_rows
from perceptual_tone.manifest import verify_baseline


def verify():
    folder = DEFAULT_RUN
    release = verify_release(DEFAULT_RELEASE)
    baseline = verify_baseline()
    rows = read_rows(DEFAULT_RELEASE / "primary.jsonl")
    all_rows = read_rows(DEFAULT_RELEASE / "manifest.jsonl")
    seen = {key: {} for key in ("speaker_id", "utterance_id", "pcm_sha256")}
    for row in all_rows:
        o = row["original"]
        part = o["partition"]
        assert o["speaker_id"] in SPEAKERS[part]
        for key, owners in seen.items():
            assert owners.setdefault(o[key], part) == part
    derivative_owners = {}
    qa = PACKAGE / "data/generated/aishell3/round2-final"
    derivatives = 0
    for row in read_rows(qa / "derived-candidates.jsonl"):
        for media in row["media"].values():
            assert file_hash(qa / media["reference"]) == media["sha256"]
            part = row["original"]["partition"]
            assert derivative_owners.setdefault(media["pcm_sha256"], part) == part
            derivatives += 1
    assert all(label_mutation_check(r) for r in rows)
    resampled_owners = {}
    resampled_checks = 0
    for row in rows:
        for view in ("target", "context"):
            values, pool, _ = input_audio(audio_contract(row), view, folder / "canonical")
            variants = [values]
            if view == "target":
                variants.append(values[pool[0] : pool[1]])
            for pcm in variants:
                sha = hashlib.sha256(pcm.tobytes()).hexdigest()
                part = row["original"]["partition"]
                assert resampled_owners.setdefault(sha, part) == part
                resampled_checks += 1
    selected = read_json(folder / "selected.json")
    results = read_json(folder / "test-results.json")
    seal = read_json(folder / "test-seal.json")
    for name, sha in seal["files"].items():
        assert file_hash(folder / name) == sha
    protocol = read_json(folder / "protocol.json")
    for name, sha in protocol["source_hashes"].items():
        assert file_hash(PACKAGE / name) == sha
    assert selected["frozen_at"] < results["evaluated_at"] < seal["frozen_at"]
    acoustic = {r["example_id"]: r for r in read_json(folder / "acoustic-baseline.json")}
    selection_rows = [r for r in rows if r["original"]["partition"] != "test"]
    test_rows = [r for r in rows if r["original"]["partition"] == "test"]
    train = np.array([r["original"]["partition"] == "train" for r in selection_rows])
    labels = np.array([r["original"]["label"] for r in selection_rows])

    def blocks(phase):
        return {
            (name, view): np.load(folder / f"{phase}-{name}-{view}.npz")["values"]
            for name in protocol["config"]["encoders"]
            for view in protocol["config"]["views"]
            if (folder / f"{phase}-{name}-{view}.npz").exists()
        }

    selection_blocks = blocks("selection")
    test_blocks = blocks("test")
    checks = {}
    for family, item in selected["models"].items():
        assert file_hash(folder / item["file"]) == item["sha256"]
        model = joblib.load(folder / item["file"])
        matrix = feature_matrix(item["config"], test_rows, acoustic, test_blocks)
        actual = probabilities(model, matrix)
        expected = np.array([r["probabilities"] for r in results["predictions"][family]])
        np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-12)
        training = feature_matrix(item["config"], selection_rows, acoustic, selection_blocks)[train]
        refit = pipeline(item["config"]["kind"], item["config"].get("C", 1.0))
        kwargs = (
            {"mlpclassifier__sample_weight": compute_sample_weight("balanced", labels[train])}
            if item["config"]["kind"] == "mlp"
            else {}
        )
        with warnings.catch_warnings(), threadpool_limits(limits=4):
            warnings.simplefilter("ignore")
            refit.fit(training, labels[train], **kwargs)
        repeated = probabilities(refit, matrix)
        np.testing.assert_allclose(repeated, expected, rtol=0, atol=1e-10)
        score = metric(
            [r["original"]["label"] for r in test_rows],
            [r["prediction"] for r in results["predictions"][family]],
            actual,
        )
        for key, value in score.items():
            assert results["metrics"][family][key] == value
        checks[family] = {
            "reload_delta": float(np.max(np.abs(actual - expected))),
            "seeded_refit_delta": float(np.max(np.abs(repeated - expected))),
        }
    caches = 0
    for metadata in (folder / "embedding-cache").glob("*.json"):
        entry = read_json(metadata)
        assert metadata.stem == entry["key"]
        assert file_hash(metadata.with_suffix(".npy")) == entry["sha256"]
        assert entry["owned_frames"] > 0
        caches += 1
    # Re-extract real speech without reusing an embedding cache, then corrupt only a
    # temporary copy to demonstrate rejection; the sealed experiment stays intact.
    fresh = {}
    for name in protocol["config"]["encoders"]:
        with tempfile.TemporaryDirectory() as tmp:
            encoder = Encoder(name, Path(tmp), folder / "canonical")
            actual, record = encoder.extract(audio_contract(selection_rows[0]), "context")
            expected = selection_blocks[(name, "context")][0]
            np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-6)
            fresh[name] = float(np.max(np.abs(actual - expected)))
            (Path(tmp) / (record["key"] + ".npy")).write_bytes(b"corrupt-test-fixture")
            try:
                encoder.extract(audio_contract(selection_rows[0]), "context")
            except ValueError as error:
                assert str(error) == "embedding_cache_corrupted"
            else:
                raise AssertionError("corrupted_embedding_was_accepted")
    external_delta = 0.0
    external = read_json(folder / "external-probe.json")
    external_seal = read_json(folder / "external-probe-seal.json")
    assert file_hash(folder / "external-probe.json") == external_seal["sha256"]
    assert seal["frozen_at"] < external["protocol"]["started_at"]
    for name, sha in external["protocol"]["sources"].items():
        assert file_hash(ROOT / name) == sha
    item = selected["models"][selected["best_family_by_validation"]]
    config = item["config"]
    model = joblib.load(folder / item["file"])
    encoder = Encoder(config["encoder"], folder / "external-embedding-cache", folder / "canonical")
    for row in external["predictions"]:
        vectors, _ = encoder.extract(row["pooling_contract"], config["view"])
        actual = probabilities(model, vectors[LAYERS.index(config["layer"])][None, :])[0]
        np.testing.assert_allclose(actual, row["probabilities"], rtol=0, atol=1e-12)
        external_delta = max(external_delta, float(np.max(np.abs(actual - row["probabilities"]))))
    return {
        "release_manifest_sha256": release["manifest_sha256"],
        "baseline": baseline,
        "primary_rows": len(rows),
        "derivative_audio_checks": derivatives,
        "resampled_model_input_audio_leakage_checks": resampled_checks,
        "embedding_cache_checks": caches,
        "class_counts": {
            p: dict(
                Counter(r["original"]["label"] for r in rows if r["original"]["partition"] == p)
            )
            for p in SPEAKERS
        },
        "prediction_reproduction": checks,
        "fresh_encoder_max_delta": fresh,
        "selection_precedes_test": True,
        "external_probe_follows_test_freeze": True,
        "external_units_reproduced": len(external["predictions"]),
        "external_probability_max_delta": external_delta,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))

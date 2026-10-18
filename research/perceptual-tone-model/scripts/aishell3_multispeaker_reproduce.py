"""Reproduce sealed probabilities and caches, with no new configuration or selection."""

import json
import sys
import tempfile
from pathlib import Path

import joblib
import numpy as np
from threadpoolctl import threadpool_limits

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aishell3_continue import stable_json
from aishell3_multispeaker_acquire import ROOT, preserve
from aishell3_multispeaker_train import PILOT_RUN, RUN, checked_release, verify_experiment_a
from perceptual_tone.aishell3_embeddings import LAYERS, Encoder
from perceptual_tone.aishell3_learning import acoustic_vector, audio_contract, pipeline
from perceptual_tone.common import file_hash, read_json, read_rows


def reproduce():
    release, _ = checked_release(ROOT)
    a = verify_experiment_a(RUN)
    if file_hash(RUN / "test-results.json") != read_json(RUN / "test-seal.json")["sha256"]:
        raise ValueError("test_result_seal_changed")
    rows = read_rows(release / "primary.jsonl")
    tv = [r for r in rows if r["original"]["partition"] != "test"]
    test = [r for r in rows if r["original"]["partition"] == "test"]
    train_mask = np.asarray([r["original"]["partition"] == "train" for r in tv])
    labels = np.asarray([r["original"]["label"] for r in tv])
    matrices, cache_keys = {}, set()
    for phase, records in (("test", test), ("train-validation", tv)):
        matrix_path = RUN / f"{phase}-chinese_hubert_base-context.npz"
        seal = read_json(matrix_path.with_suffix(".json"))
        if file_hash(matrix_path) != seal["sha256"] or seal["ids"] != [
            r["example_id"] for r in records
        ]:
            raise ValueError("feature_matrix_seal_or_row_order_changed")
        values = np.load(matrix_path, allow_pickle=False)["values"]
        for i, entry in enumerate(seal["records"]):
            key = entry["key"]
            cache_keys.add(key)
            meta = read_json(RUN / "embedding-cache" / (key + ".json"))
            path = RUN / "embedding-cache" / (key + ".npy")
            if meta["key"] != key or file_hash(path) != meta["sha256"] or meta["owned_frames"] < 1:
                raise ValueError("cache_identity_or_integrity_failure")
            np.testing.assert_array_equal(values[i], np.load(path, allow_pickle=False))
        matrices[phase] = values[:, LAYERS.index(9), :]
    acoustic = {}
    for phase in ("train-validation", "test"):
        folder = RUN / (phase + "-acoustics")
        if (
            file_hash(folder / "acoustic-baseline.json")
            != read_json(folder / "acoustic-seal.json")["sha256"]
        ):
            raise ValueError("acoustic_cache_changed")
        by_id = {r["example_id"]: r for r in read_json(folder / "acoustic-baseline.json")}
        acoustic[phase] = np.stack(
            [
                acoustic_vector(by_id[r["example_id"]])[1]
                for r in (tv if phase == "train-validation" else test)
            ]
        )
    old = read_json(PILOT_RUN / "selected.json")["models"]["model2_hubert"]
    freeze = read_json(RUN / "models-frozen.json")
    checks = {}
    configs = (
        ("experiment_A", PILOT_RUN / old["file"], matrices["test"], None, None),
        (
            "experiment_B",
            RUN / freeze["models"]["experiment_B"]["file"],
            matrices["test"],
            matrices["train-validation"],
            0.1,
        ),
        (
            "acoustic_LR",
            RUN / freeze["models"]["acoustic_LR"]["file"],
            acoustic["test"],
            acoustic["train-validation"],
            1.0,
        ),
    )
    for name, path, test_values, tv_values, C in configs:
        pred_path = RUN / (
            "experiment-A-predictions.json"
            if name == "experiment_A"
            else name + "-test-predictions.json"
        )
        saved = np.asarray(read_json(pred_path)["probabilities"])
        model = joblib.load(path)
        with threadpool_limits(limits=4):
            actual = model.predict_proba(test_values)
            np.testing.assert_allclose(actual, saved, atol=1e-12, rtol=0)
            checks[name] = {
                "reload_max_probability_delta": float(np.max(np.abs(actual - saved))),
                "model_sha256": file_hash(path),
            }
            if C is not None:
                # Explicit requested reproduction only: same train rows/seed/C, no selection.
                refit = pipeline("logistic", C).fit(tv_values[train_mask], labels[train_mask])
                repeated = refit.predict_proba(test_values)
                np.testing.assert_allclose(repeated, saved, atol=1e-10, rtol=0)
                checks[name]["seeded_refit_max_probability_delta"] = float(
                    np.max(np.abs(repeated - saved))
                )
    with tempfile.TemporaryDirectory(prefix="cache-reproduction-", dir=ROOT) as tmp:
        encoder = Encoder("chinese_hubert_base", Path(tmp), RUN / "canonical")
        fresh, meta = encoder.extract(audio_contract(tv[0]), "context")
        original = np.load(
            RUN / "train-validation-chinese_hubert_base-context.npz", allow_pickle=False
        )["values"][0]
        np.testing.assert_allclose(fresh, original, atol=1e-6, rtol=0)
        cached, _ = encoder.extract(audio_contract(tv[0]), "context")
        np.testing.assert_array_equal(cached, fresh)
        corrupt_path = Path(tmp) / (meta["key"] + ".npy")
        raw = bytearray(corrupt_path.read_bytes())
        raw[-1] ^= 1
        corrupt_path.write_bytes(raw)
        try:
            encoder.extract(audio_contract(tv[0]), "context")
        except ValueError as error:
            if str(error) != "embedding_cache_corrupted":
                raise
        else:
            raise ValueError("corrupt_cache_was_not_rejected")
    canonical = list((RUN / "canonical").glob("*.json"))
    for meta in canonical:
        if file_hash(meta.with_suffix(".wav")) != read_json(meta)["wav_sha256"]:
            raise ValueError("canonical_audio_cache_changed")
    history = preserve(ROOT)
    verify_experiment_a(RUN)
    result = {
        "status": "PASS",
        "cache_entries_verified": len(cache_keys),
        "canonical_audio_entries": len(canonical),
        "models": checks,
        "fresh_embedding_max_delta": float(np.max(np.abs(fresh - original))),
        "cache_repeat_exact": True,
        "temporary_cache_corruption_rejected": True,
        "tolerances": {"reload": 1e-12, "seeded_refit": 1e-10, "fresh_embedding": 1e-6, "rtol": 0},
        "experiment_A_sealed_before_B": a["status"],
        "history": history,
        "configuration_searches": 0,
        "new_results_selected": False,
    }
    stable_json(ROOT / "reproduction.json", result)
    return result


if __name__ == "__main__":
    print(json.dumps(reproduce(), indent=2))

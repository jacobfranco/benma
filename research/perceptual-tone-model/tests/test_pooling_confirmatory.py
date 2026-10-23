"""Focused confirmatory invariants; no product/mobile or fitting tests."""

import hashlib
import inspect
import json
import unittest

import numpy as np
from perceptual_tone.common import PACKAGE, ROOT, digest, file_hash, read_json, read_rows
from perceptual_tone.pooling_confirmatory import (
    ARMS,
    LOCK,
    OUT,
    PRIOR,
    STATES,
    remaining_native,
    variant,
)
from perceptual_tone.pooling_representation import acoustic_features, representation


class ConfirmatoryRulesTests(unittest.TestCase):
    def example(self, state, n=5, arm=ARMS[1], ownership="safe", owner=None):
        centers = 0.01 + np.arange(n) * 0.02
        features = [
            {"time": t, "rms_20ms": i + 1, "high_band_fraction": 0.25}
            for i, t in enumerate(centers)
        ]
        return variant(
            arm, state, ownership, owner or [0, n * 0.02], np.arange(n), centers, features
        )

    def test_exact_native_complement_and_order_independence(self):
        lock = read_json(LOCK)
        rows = read_rows(ROOT / lock["native_release"] / "manifest.jsonl")
        prior = read_json(PRIOR / "native-control-ids.json")["ids"]
        intended = {
            r["example_id"]
            for r in rows
            if r["primary_eligible"] and r["original"]["partition"] == "test"
        }
        actual = [r["example_id"] for r in remaining_native(rows, prior)]
        self.assertEqual(len(actual), 659)
        self.assertFalse(set(actual) & set(prior))
        self.assertEqual(set(actual) | set(prior), intended)
        self.assertEqual(
            actual, [r["example_id"] for r in remaining_native(rows[::-1], prior[::-1])]
        )
        if (OUT / "native-ids.json").exists():
            self.assertEqual(actual, read_json(OUT / "native-ids.json")["ids"])

    def test_one_frame_left_and_right_unchanged_owner(self):
        for a in ARMS:
            for state, expected in zip(
                STATES, [list(range(5)), [1, 2, 3, 4], [0, 1, 2, 3]], strict=True
            ):
                r = self.example(state, arm=a)
                self.assertEqual(r["frame_ids"], expected)
                self.assertEqual(r["eligible_frame_ids"], list(range(5)))
                self.assertEqual(r["ownership_span"], [0, 0.1])
                self.assertIsNone(r["abstention_reason"])

    def test_support_minimum_including_clipped_three_frames(self):
        for state in STATES[1:]:
            self.assertEqual(
                self.example(state, n=3)["abstention_reason"], "perturbation_not_admissible"
            )
            self.assertIsNone(self.example(state, n=4)["abstention_reason"])
        # Three frames remain, but clipping the owner's right edge leaves only 55ms.
        r = self.example("CONTRACT_LEFT", n=4, owner=[0, 0.075])
        self.assertEqual(r["frame_count"], 3)
        self.assertAlmostEqual(r["support_ms"], 55)
        self.assertEqual(r["abstention_reason"], "perturbation_not_admissible")

    def test_ownership_abstention_never_rescued(self):
        for a in ARMS:
            for s in STATES:
                r = self.example(s, arm=a, ownership="ambiguous")
                self.assertEqual(r["abstention_reason"], "ownership_ambiguous")
                self.assertEqual(r["frame_ids"], list(range(5)))

    def test_only_two_arms_and_three_variants(self):
        with self.assertRaises(ValueError):
            self.example("BASE", arm="CENTRAL_HALF")
        with self.assertRaises(ValueError):
            self.example("EXPAND_LEFT")

    def test_acoustic_formula_is_unchanged_and_features_match(self):
        freeze = read_json(PRIOR / "preregistration.json")["code_hashes"]
        path = PACKAGE / "perceptual_tone/pooling_representation.py"
        self.assertEqual(file_hash(path), freeze[str(path)])
        from perceptual_tone.ownership_diagnostics import features

        values = np.random.default_rng(13).normal(size=3200)
        expected = [
            {k: r[k] for k in ("time", "rms_20ms", "high_band_fraction")}
            for r in features(values, 16000)
        ]
        self.assertEqual(acoustic_features(values, 16000), expected)
        for a in ARMS:
            for s in STATES:
                r = self.example(s, arm=a)
                centers = 0.01 + np.arange(5) * 0.02
                f = [
                    {"time": t, "rms_20ms": i + 1, "high_band_fraction": 0.25}
                    for i, t in enumerate(centers)
                ]
                old = representation(a, "safe", [0, 0.1], r["frame_ids"], centers, f)
                for key in old.keys() - {"eligible_frame_ids"}:
                    self.assertEqual(r[key], old[key])

    def test_no_f0_expected_character_prediction_dependency(self):
        self.assertEqual(
            list(inspect.signature(variant).parameters),
            ["arm", "state", "ownership", "owner_span", "ids", "centers", "features"],
        )
        centers = 0.01 + np.arange(5) * 0.02
        features = [{"time": t, "rms_20ms": 1, "high_band_fraction": 0.2} for t in centers]
        poison = [
            {
                **r,
                "f0": 999,
                "expected_tone": "T4",
                "lexical_tone": "T1",
                "grade": "wrong",
                "character": "买",
                "prediction": "T2",
            }
            for r in features
        ]
        for a in ARMS:
            for s in STATES:
                args = (a, s, "safe", [0, 0.1], np.arange(5), centers)
                self.assertEqual(variant(*args, features), variant(*args, poison))


class ConfirmatorySealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (OUT / "representation-manifest-seal.json").exists():
            raise unittest.SkipTest("confirmatory manifest not yet sealed")
        cls.manifest = read_json(OUT / "representation-manifest.json")
        cls.plan = read_json(OUT / "preregistration.json")

    def test_all_items_all_six_conditions(self):
        for item in self.plan["items"]:
            rows = [
                r for r in self.manifest["records"] if r["id"] == item["id"] and r["arm"] in ARMS
            ]
            self.assertEqual(
                {(r["arm"], r["perturbation"]) for r in rows},
                {(a, s) for a in ARMS for s in STATES},
            )
            self.assertEqual(len(rows), 6)
            for r in rows:
                self.assertEqual(r["ownership_span"], item["contract"]["pooling"])
                self.assertEqual(r["ownership"], item["ownership"])

    def test_manifest_determinism_and_vector_reconstruction(self):
        from perceptual_tone.frame_attribution import geometry

        items = {i["id"]: i for i in self.plan["items"]}
        hidden_cache = {}
        for r in self.manifest["records"]:
            if r["arm"] not in ARMS:
                continue
            centers, ids = geometry(items[r["id"]]["contract"])
            # Map from BASE audit to retain every original timestamp deterministically.
            base = next(
                x
                for x in self.manifest["records"]
                if x["id"] == r["id"] and x["arm"] == r["arm"] and x["perturbation"] == "BASE"
            )
            audit = base["acoustic_audit"]
            f = [
                dict(time=t, rms_20ms=rms, high_band_fraction=h)
                for t, rms, h in zip(
                    audit["mapped_timestamps"],
                    audit["rms_20ms"],
                    audit["high_band_fraction"],
                    strict=True,
                )
            ]
            rebuilt = variant(
                r["arm"], r["perturbation"], r["ownership"], r["ownership_span"], ids, centers, f
            )
            self.assertEqual(digest(rebuilt), digest({k: r[k] for k in rebuilt}))
            if r["pooled_vector"] is not None:
                if r["hidden_path"] not in hidden_cache:
                    hidden_cache[r["hidden_path"]] = np.load(r["hidden_path"], allow_pickle=False)
                hidden = hidden_cache[r["hidden_path"]]
                expected = np.array(r["normalized_weights"]) @ hidden[r["frame_ids"]].astype(float)
                np.testing.assert_array_equal(expected, r["pooled_vector"])

    def test_manifest_hash_reproducible_and_seal_precedes_heads(self):
        seal = read_json(OUT / "representation-manifest-seal.json")
        serialized = (
            json.dumps(self.manifest, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
            + "\n"
        )
        self.assertEqual(hashlib.sha256(serialized.encode()).hexdigest(), seal["sha256"])
        self.assertEqual(file_hash(OUT / "representation-manifest.json"), seal["sha256"])
        self.assertFalse(seal["classifier_loaded"])
        self.assertEqual(seal["row_count"], len(self.manifest["records"]))
        if (OUT / "inference-start.json").exists():
            start = read_json(OUT / "inference-start.json")
            self.assertLess(seal["sealed_at"], start["started_at"])
            self.assertEqual(start["manifest_sha256"], seal["sha256"])

    def test_models_prior_code_audio_and_manifest_unchanged(self):
        from perceptual_tone.pooling_confirmatory import verify_manifest

        verify_manifest()
        lock = read_json(LOCK)
        self.assertEqual(self.manifest["encoder_weights"], lock["encoder_weights"])
        for spec in lock["model_method"]["models"].values():
            self.assertEqual(file_hash(spec["path"]), spec["sha256"])

    def test_actual_encoder_checkpoint_and_reference_archive_hashes(self):
        lock = read_json(LOCK)
        revision = lock["model_method"]["encoder"]["revision"]
        snapshot = (
            PACKAGE
            / ".cache/huggingface/models--TencentGameMate--chinese-hubert-base/snapshots"
            / revision
        )
        for name, sha in lock["encoder_weights"].items():
            self.assertEqual(file_hash(snapshot / name), sha)
        archive = (
            PACKAGE
            / "models/generated/aishell3-multispeaker-fixed-v2/test-chinese_hubert_base-context.npz"
        )
        self.assertEqual(file_hash(archive), self.manifest["native_reference_archive_sha256"])
        self.assertLess(self.manifest["native_reference_max_reextraction_error"], 1e-6)

    def test_disjoint_learner_recordings(self):
        proof = read_json(OUT / "disjoint-learner-ids.json")
        self.assertEqual(len(proof["ids"]), 27)
        self.assertFalse(any(r["overlap"] for r in proof["audit"]))
        self.assertEqual(len({r["source_id"] for r in proof["audit"]}), 5)

    def test_google_and_ambiguous_owner_semantics(self):
        for r in self.manifest["records"]:
            if r["arm"] not in ARMS:
                continue
            if r["id"] == "take-2-2":
                self.assertEqual(r["abstention_reason"], "ownership_ambiguous")
                self.assertIsNone(r["pooled_vector"])
            if r["id"] == "google-2":
                self.assertIsNone(r["abstention_reason"])
                self.assertIsNotNone(r["pooled_vector"])

    def test_predictions_exactly_cover_head_compatible_usable_rows(self):
        if not (OUT / "predictions.json").exists():
            self.skipTest("inference not run yet")
        meta = read_json(OUT / "evaluation-metadata.json")
        expected = {
            (r["id"], r["arm"], r["perturbation"], h)
            for r in self.manifest["records"]
            if r["pooled_vector"] is not None and meta[r["id"]]["head_compatible"]
            for h in ("expanded", "pilot")
        }
        rows = read_json(OUT / "predictions.json")["rows"]
        actual = {(r["id"], r["arm"], r["perturbation"], r["head"]) for r in rows}
        self.assertEqual(len(actual), len(rows))
        self.assertEqual(actual, expected)
        for r in rows:
            self.assertEqual(r["classes"], ["T1", "T2", "T3", "T4"])
            self.assertAlmostEqual(sum(r["probabilities"]), 1)

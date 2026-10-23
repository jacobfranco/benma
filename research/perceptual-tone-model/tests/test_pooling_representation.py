"""Focused offline pooling invariants; no fitting or product runtime tests."""

import copy
import inspect
import unittest

import numpy as np
from perceptual_tone.common import PACKAGE, digest, file_hash, read_json, read_rows
from perceptual_tone.pooling_representation import (
    ARMS,
    MIN_SECONDS,
    acoustic_features,
    acoustic_weights,
    central_half,
    map_acoustics,
    native_subset,
    representation,
)


class PoolingRulesTests(unittest.TestCase):
    def test_central_odd_even_and_ties(self):
        expected = {
            0: [],
            1: [0],
            2: [0],
            3: [0, 1],
            4: [1, 2],
            5: [1, 2, 3],
            6: [1, 2, 3],
            7: [1, 2, 3, 4],
            11: list(range(2, 8)),
            17: list(range(4, 13)),
        }
        for n, ids in expected.items():
            self.assertEqual(central_half(range(n)).tolist(), ids)

    def test_weights_and_invalid_numeric_clamps(self):
        np.testing.assert_array_equal(acoustic_weights([2, 4, 3], [0.25, 0.5, 1]), [1.5, 2, 0])
        np.testing.assert_array_equal(acoustic_weights([-1, 1, 1], [0, -1, 2]), [0, 1, 0])
        with self.assertRaises(ValueError):
            acoustic_weights([np.nan], [0])

    def test_existing_acoustic_equations(self):
        from perceptual_tone.ownership_diagnostics import features

        values = np.random.default_rng(42).normal(0, 0.1, 3200)
        actual = acoustic_features(values, 16000)
        expected = [
            {k: r[k] for k in ("time", "rms_20ms", "high_band_fraction")}
            for r in features(values, 16000)
        ]
        self.assertEqual(actual, expected)

    def test_mapping_tie_and_no_interpolation(self):
        features = [{"time": 0}, {"time": 2}]
        self.assertEqual(map_acoustics([1, 1.1], features), features)

    def example(self, arm, n=8, ownership="safe", zero=False):
        centers = 0.01 + np.arange(n) * 0.02
        features = [
            {"time": t, "rms_20ms": 0 if zero else i + 1, "high_band_fraction": 0.25}
            for i, t in enumerate(centers)
        ]
        return representation(arm, ownership, [0, n * 0.02], range(n), centers, features)

    def test_normalization_and_effective_support(self):
        for arm in ARMS:
            r = self.example(arm)
            w = np.array(r["normalized_weights"])
            self.assertAlmostEqual(w.sum(), 1)
            self.assertAlmostEqual(r["effective_n"], 1 / (w @ w))
        self.assertLess(self.example(ARMS[2])["effective_n"], 8)

    def test_no_zero_fallback(self):
        self.assertEqual(
            self.example(ARMS[2], zero=True)["abstention_reason"], "zero_usable_weight"
        )

    def test_ownership_ambiguity_preserved(self):
        for arm in ARMS:
            self.assertEqual(
                self.example(arm, ownership="ambiguous")["abstention_reason"], "ownership_ambiguous"
            )

    def test_60ms_no_outward_expansion(self):
        self.assertEqual(MIN_SECONDS, 0.060)
        self.assertIsNone(self.example(ARMS[0], n=3)["abstention_reason"])
        self.assertEqual(
            self.example(ARMS[1], n=4)["abstention_reason"], "insufficient_60ms_support"
        )
        self.assertEqual(len(self.example(ARMS[1], n=4)["frame_ids"]), 2)
        self.assertIsNone(self.example(ARMS[1], n=5)["abstention_reason"])

    def test_no_pitch_target_lexical_output_inputs(self):
        self.assertEqual(
            list(inspect.signature(representation).parameters),
            ["arm", "ownership", "owner_span", "ids", "centers", "features"],
        )
        centers = np.array([0.01, 0.03, 0.05, 0.07])
        clean = [{"time": t, "rms_20ms": 1, "high_band_fraction": 0.5} for t in centers]
        poisoned = [
            {
                **r,
                "f0": 500,
                "tone": "T4",
                "expected": "T1",
                "grade": "bad",
                "prediction": "T3",
                "character": "买",
            }
            for r in clean
        ]
        for arm in ARMS:
            args = (arm, "safe", [0, 0.08], range(4), centers)
            self.assertEqual(representation(*args, clean), representation(*args, poisoned))

    def test_deterministic_native_selection(self):
        lock = read_json(PACKAGE / "configs/dev-learned-lock.json")
        from perceptual_tone.common import ROOT

        rows = read_rows(ROOT / lock["native_release"] / "manifest.jsonl")
        expected = [r["example_id"] for r in native_subset(rows)]
        self.assertEqual(expected, [r["example_id"] for r in native_subset(rows[::-1])])
        changed = copy.deepcopy(rows)
        for r in changed:
            r["prediction"] = "T2"
            r["original"]["hanzi"] = "changed"
        self.assertEqual(expected, [r["example_id"] for r in native_subset(changed)])
        self.assertEqual(len(set(expected)), 256)


class SealedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from perceptual_tone.pooling_experiment import OUT

        cls.out = OUT
        if not (OUT / "representation-manifest-seal.json").exists():
            raise unittest.SkipTest("representations not yet sealed")
        cls.manifest = read_json(OUT / "representation-manifest.json")

    def test_seal_precedes_inference(self):
        seal = read_json(self.out / "representation-manifest-seal.json")
        self.assertEqual(seal["sha256"], file_hash(self.out / "representation-manifest.json"))
        if (self.out / "inference-start.json").exists():
            start = read_json(self.out / "inference-start.json")
            self.assertLess(seal["sealed_at"], start["started_at"])
            self.assertEqual(seal["sha256"], start["manifest_sha256"])

    def test_manifest_reproducibility(self):
        for r in self.manifest["records"]:
            if r["arm"] == "CURRENT_REFERENCE" or r["ownership"] != "safe":
                continue
            ids = r["eligible_frame_ids"]
            centers = np.zeros(max(ids) + 1)
            # Reconstruct full centers from sealed uniform record, without predictions.
            full = next(
                x for x in self.manifest["records"] if x["id"] == r["id"] and x["arm"] == ARMS[0]
            )
            centers[full["frame_ids"]] = full["frame_centers"]
            rebuilt = representation(
                r["arm"],
                r["ownership"],
                r["ownership_span"],
                ids,
                centers,
                r["mapped_acoustics"] or [],
            )
            original = {k: r[k] for k in rebuilt}
            self.assertEqual(digest(rebuilt), digest(original))

    def test_artifact_hashes_and_models_unchanged(self):
        from perceptual_tone.pooling_experiment import verify_manifest

        verify_manifest()

    def test_all_twenty_units_and_ambiguous_buy(self):
        rows = [
            r for r in self.manifest["records"] if r["dataset"] == "physical" and r["arm"] in ARMS
        ]
        self.assertEqual(len(rows), 60)
        for r in rows:
            if r["id"] == "take-2-2":
                self.assertEqual(r["abstention_reason"], "ownership_ambiguous")
                self.assertIsNone(r["vector_path"])

    def test_neutral_representations_are_not_head_abstentions(self):
        metadata = read_json(self.out / "evaluation-metadata.json")
        neutral_ids = {i for i, m in metadata.items() if not m["head_compatible"]}
        self.assertEqual(len(neutral_ids), 4)
        for r in self.manifest["records"]:
            if r["id"] in neutral_ids and r["arm"] in ARMS:
                self.assertIsNone(r["abstention_reason"])
                self.assertIsNotNone(r["vector_path"])
        predictions = read_json(self.out / "predictions.json")["rows"]
        self.assertFalse(neutral_ids & {r["id"] for r in predictions})
        keys = [(r["id"], r["arm"], r["head"]) for r in predictions]
        self.assertEqual(len(keys), len(set(keys)))

    def test_pooled_vectors_reconstruct_exactly(self):
        plan = read_json(self.out / "preregistration.json")
        indices = {i["id"]: n for n, i in enumerate(plan["items"])}
        for r in self.manifest["records"]:
            if r["vector_path"] is None:
                continue
            hidden = np.load(
                self.out / f"representations/{indices[r['id']]:04}-layer9.npy",
                allow_pickle=False,
            )
            if r["arm"] == "CURRENT_REFERENCE":
                expected = hidden[r["frame_ids"]].astype(float).mean(0)
            else:
                weights = np.array(r["normalized_weights"])
                self.assertAlmostEqual(weights.sum(), 1)
                expected = weights @ hidden[r["frame_ids"]].astype(float)
            np.testing.assert_array_equal(np.load(r["vector_path"], allow_pickle=False), expected)

    def test_preinference_inventory_and_report_preserved(self):
        import hashlib

        from perceptual_tone.pooling_experiment import verify_files

        seal = read_json(self.out / "pre-inference-inventory-seal.json")
        verify_files({str(self.out / "pre-inference-inventory.json"): seal["sha256"]})
        start = read_json(self.out / "inference-start.json")
        report = read_json(self.out / "pre-inference-report-seal.json")
        self.assertLess(report["recorded_at"], start["started_at"])
        prefix = (PACKAGE / "pooling-representation-experiment-report.md").read_bytes()[
            : report["bytes"]
        ]
        self.assertEqual(hashlib.sha256(prefix).hexdigest(), report["sha256"])

    def test_sealed_native_ids_unchanged(self):
        from perceptual_tone.common import ROOT

        lock = read_json(PACKAGE / "configs/dev-learned-lock.json")
        rows = read_rows(ROOT / lock["native_release"] / "manifest.jsonl")
        selected = [r["example_id"] for r in native_subset(rows)]
        self.assertEqual(selected, read_json(self.out / "native-control-ids.json")["ids"])


if __name__ == "__main__":
    unittest.main()

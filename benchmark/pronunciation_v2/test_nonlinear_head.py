"""Focused Experiment 3 tests; nonlinear fitting uses synthetic data only."""

import ast
import copy
import tempfile
import unittest
from pathlib import Path

import nonlinear_head as head
import nonlinear_sources as sources
import numpy as np
import torch


class HeadTests(unittest.TestCase):
    def test_exact_baseline_config(self):
        self.assertEqual(
            dict(head.CLASSIFIER),
            dict(
                C=0.1,
                solver="lbfgs",
                penalty="l2",
                class_weight=None,
                fit_intercept=True,
                max_iter=3000,
                tol=1e-8,
                random_state=20260929,
            ),
        )
        self.assertEqual(dict(head.SCALER), dict(copy=True, with_mean=True, with_std=True))
        self.assertEqual(head.REVISION, "0b5b8e868dd84f03fd87d01f9c4ff0f080fecfe8")
        self.assertEqual(head.PREPROCESSING["sample_rate"], 16000)
        self.assertFalse(head.PREPROCESSING["trim"])

    def test_shape_capacity_initialization(self):
        model = head.make_head()
        self.assertEqual(
            [type(x) for x in model], [torch.nn.Linear, torch.nn.Tanh, torch.nn.Linear]
        )
        self.assertEqual(sum(p.numel() for p in model.parameters()), 6188)
        self.assertEqual(tuple(model(torch.zeros(7, 768)).shape), (7, 4))
        self.assertEqual(tuple(model[0].weight.shape), (8, 768))
        self.assertTrue(torch.equal(model[0].bias, torch.zeros(8)))
        self.assertTrue(torch.equal(model[2].bias, torch.zeros(4)))
        self.assertTrue(
            all(p.device.type == "cpu" and p.dtype == torch.float32 for p in model.parameters())
        )

    def test_fixed_seed_and_training_learns_deterministically(self):
        rng = np.random.default_rng(17)
        y = np.tile(np.arange(1, 5), 20)
        x = rng.normal(0, 0.02, (80, 768)).astype("float32")
        x[np.arange(80), y - 1] += 2
        a, losses_a = head.fit_standardized(x, y)
        torch.manual_seed(98)
        b, losses_b = head.fit_standardized(x, y)
        self.assertEqual(head.CONFIG["seed"], 20261001)
        self.assertEqual(len(losses_a), 200)
        self.assertEqual(losses_a, losses_b)
        self.assertLess(losses_a[-1], losses_a[0])
        for key, value in a.state_dict().items():
            self.assertTrue(torch.equal(value, b.state_dict()[key]))
        with torch.inference_mode():
            self.assertGreater(
                float((a(torch.from_numpy(x)).argmax(1).numpy() == y - 1).mean()), 0.9
            )

    def test_reject_bad_features_and_labels(self):
        for x, y in (
            (np.zeros((4, 2304)), np.arange(1, 5)),
            (np.full((4, 768), np.nan), np.arange(1, 5)),
            (np.zeros((4, 768)), np.arange(2, 6)),
            (np.zeros((4, 768)), np.array([1.0, 2.0, 3.0, 4.0])),
        ):
            with self.assertRaises(ValueError):
                head.fit_standardized(x, y)

    def test_exact_training_rows_and_opened_eval_guard(self):
        original = head.authoritative_rows()
        train = [r for r in original if r["partition"] == "train"]
        head.validate_training(train)
        for partition in ("validation", "test"):
            changed = copy.deepcopy(train)
            changed[0] = next(r for r in original if r["partition"] == partition)
            with self.assertRaises(ValueError):
                head.validate_training(changed)
        opened = head.csv_rows(
            head.ROOT
            / "docs/research/pronunciation-v2/2026-09-30-experiment-2-preflight"
            / "sealed-test-manifest.csv"
        )
        changed = copy.deepcopy(train)
        changed[0] = dict(opened[0], partition="train")
        with self.assertRaises(ValueError):
            head.validate_training(changed)
        for key, value in (("tone", "5"), ("speaker_id", "impostor"), ("audio_sha256", "changed")):
            changed = copy.deepcopy(train)
            changed[0][key] = value
            with self.assertRaises(ValueError):
                head.validate_training(changed)
        with self.assertRaises(ValueError):
            head.validate_training(train[::-1])

    def test_comparison_all_metrics_and_pairing(self):
        rows = [dict(source_asset_id=str(i), speaker_id="s", tone=str(i + 1)) for i in range(4)]
        result = head.comparison(rows, [1, 3, 3, 1], [1, 2, 4, 1])
        self.assertEqual(
            result["paired_correctness"],
            dict(
                both_correct=1,
                A_only_correct=1,
                B_only_correct=1,
                both_wrong=1,
            ),
        )
        self.assertEqual(result["A"]["directed_confusions"]["T2->T3"]["count"], 1)
        self.assertEqual(result["B"]["directed_confusions"]["T3->T4"]["count"], 1)
        self.assertEqual(set(result["A"]["per_tone"]), {"1", "2", "3", "4"})
        self.assertIn("s", result["per_speaker"])


def candidates():
    result = []
    for s in range(3):
        for tone in range(1, 5):
            for i in range(12):
                asset = f"new-{s}-{tone}-{i}"
                row = dict.fromkeys(sources.REQUIRED, "evidence")
                row.update(
                    source_asset_id=asset,
                    source_sha1=asset,
                    speaker_id=f"new:{s}",
                    speaker_name=f"New {s}",
                    text=f"word-{tone}-{i}",
                    tone=str(tone),
                    metadata_status="eligible",
                )
                result.append(row)
    return result


class SourceTests(unittest.TestCase):
    def test_speaker_disjointness_by_id_and_normalized_alias(self):
        for speaker in sources.PRIOR_IDS:
            self.assertTrue(
                sources.previously_used(dict(speaker_id=speaker, speaker_name="unknown"))
            )
        for name in (
            "Wei Gao",
            "CanonNi",
            "Levi Highway",
            "Luilui6666",
            "Jouketou",
            "雲角",
            "Fake_estate",
        ):
            self.assertTrue(sources.previously_used(dict(speaker_id="new", speaker_name=name)))
        rows = candidates()
        for r in rows[:48]:
            r["speaker_id"] = "lingualibre:Q1332695"
        self.assertEqual(sources.choose(rows), [])

    def test_deterministic_selection_ignores_all_prediction_fields(self):
        rows = candidates()
        expected = [r["source_asset_id"] for r in sources.choose(rows)]
        self.assertEqual(len(expected), 120)
        altered = copy.deepcopy(rows[::-1])
        for i, row in enumerate(altered):
            row.update(prediction=i % 4 + 1, probability=i / len(rows), correct=bool(i % 2))
        self.assertEqual([r["source_asset_id"] for r in sources.choose(altered)], expected)

    def test_tiny_speakers_and_duplicate_targets_cannot_fill_quota(self):
        self.assertEqual(sources.choose(candidates()[:48]), [])
        self.assertEqual(sources.choose([r for r in candidates() if r["tone"] == "1"]), [])
        rows = candidates()
        for r in rows:
            r["text"] = "same"
        self.assertEqual(sources.choose(rows), [])

    def test_required_provenance_and_tones(self):
        for key in sources.REQUIRED:
            rows = candidates()
            rows[0][key] = ""
            with self.assertRaises(ValueError):
                sources.choose(rows)
        for tone in ("0", "5", "T2", "unknown"):
            rows = candidates()
            rows[0]["tone"] = tone
            with self.assertRaises(ValueError):
                sources.choose(rows)

    def test_metadata_auditor_has_no_model_imports(self):
        tree = ast.parse(Path(sources.__file__).read_text())
        imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        imports |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        self.assertTrue(
            imports.isdisjoint({"torch", "numpy", "nonlinear_head", "model_probe", "features"})
        )

    def test_immutable_write_does_not_replace_a_seal(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sealed-test-manifest.csv"
            sources.immutable_write(path, b"original\n")
            sources.immutable_write(path, b"original\n")
            with self.assertRaises((ValueError, FileExistsError)):
                sources.immutable_write(path, b"replacement\n")
            self.assertEqual(path.read_bytes(), b"original\n")


if __name__ == "__main__":
    unittest.main()

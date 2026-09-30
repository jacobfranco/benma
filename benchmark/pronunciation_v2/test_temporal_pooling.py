"""Synthetic scientific-control tests; never open fresh evaluation features."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import temporal_pooling as experiment
import torch
from features import freeze, state_digest
from transformers import Wav2Vec2Config, Wav2Vec2FeatureExtractor, Wav2Vec2Model


class PoolingTests(unittest.TestCase):
    def test_exact_bin_membership_and_dimensions(self):
        expected = {
            3: ([0], [1], [2]),
            4: ([0], [1], [2, 3]),
            5: ([0], [1, 2], [3, 4]),
            6: ([0, 1], [2, 3], [4, 5]),
            7: ([0, 1], [2, 3], [4, 5, 6]),
            8: ([0, 1], [2, 3, 4], [5, 6, 7]),
        }
        for n, groups in expected.items():
            with self.subTest(n=n):
                # Distinct basis vectors prove membership, not just an average index.
                hidden = torch.zeros(n, 768)
                hidden[:, :n] = torch.eye(n)
                result = experiment.pool_frames(hidden)
                self.assertEqual(result["A"].shape, (768,))
                self.assertEqual(result["B"].shape, (2304,))
                np.testing.assert_array_equal(result["A"], hidden.mean(0).numpy())
                for j, indices in enumerate(groups):
                    wanted = np.zeros(768, dtype=np.float32)
                    wanted[indices] = 1 / len(indices)
                    np.testing.assert_array_equal(result["B"][j * 768 : (j + 1) * 768], wanted)

    def test_fewer_than_three_fails_both_arms(self):
        for n in (0, 1, 2):
            with self.subTest(n=n), self.assertRaisesRegex(ValueError, "both arms"):
                experiment.pool_frames(torch.zeros(n, 768))

    def test_invalid_hidden_input(self):
        for hidden in (torch.zeros(1, 3, 768), torch.full((3, 768), float("nan"))):
            with self.assertRaises(ValueError):
                experiment.pool_frames(hidden)

    def test_deterministic_frozen_single_clip_forward(self):
        torch.manual_seed(4)
        torch.set_num_threads(1)
        model = freeze(
            Wav2Vec2Model(
                Wav2Vec2Config(
                    hidden_size=16,
                    num_hidden_layers=8,
                    num_attention_heads=2,
                    intermediate_size=24,
                    conv_dim=(8, 8, 8),
                    conv_stride=(5, 2, 2),
                    conv_kernel=(10, 3, 3),
                    num_conv_pos_embeddings=8,
                    num_conv_pos_embedding_groups=2,
                    attn_implementation="eager",
                )
            )
        )
        processor = Wav2Vec2FeatureExtractor(return_attention_mask=False)
        wave = np.random.default_rng(4).normal(size=1000).astype(np.float32)
        before = state_digest(model)
        a, n = experiment.encode_pair(model, processor, wave)
        b, repeat_n = experiment.encode_pair(model, processor, wave)
        self.assertEqual(n, repeat_n)
        for arm in "AB":
            np.testing.assert_array_equal(a[arm], b[arm])
        self.assertEqual(before, state_digest(model))
        self.assertTrue(all(p.grad is None and not p.requires_grad for p in model.parameters()))
        model.train()
        with self.assertRaisesRegex(ValueError, "frozen"):
            experiment.encode_pair(model, processor, wave)


class FirewallTests(unittest.TestCase):
    def test_fixed_config_immutable(self):
        with self.assertRaises(TypeError):
            experiment.CLASSIFIER["C"] = 1.0
        self.assertEqual(
            dict(experiment.CLASSIFIER),
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

    def test_scaler_uses_training_only_and_rejects_evaluation_ids(self):
        rng = np.random.default_rng(1)
        train = rng.normal(size=(40, 8))
        x = np.vstack([train, np.full((1, 8), 1e9)])
        rows = [
            dict(
                source_asset_id=str(i),
                partition="train",
                speaker_id="shtooka:wei-gao",
                tone=i % 4 + 1,
            )
            for i in range(40)
        ]
        rows.append(
            dict(
                source_asset_id="eval",
                partition="validation",
                speaker_id="lingualibre:Q1573006",
                tone=1,
            )
        )
        ids = {str(i) for i in range(40)}
        arrays, metadata = experiment.fit_fixed(x, rows, ids)
        np.testing.assert_array_equal(arrays["mean"], train.mean(0))
        np.testing.assert_array_equal(arrays["var"], train.var(0))
        self.assertEqual(int(arrays["n_samples_seen"]), 40)
        self.assertEqual(metadata["training_rows"], 40)
        for changed in (ids | {"eval"}, ids | {"missing"}):
            with self.assertRaises(ValueError):
                experiment.fit_fixed(x, rows, changed)

    def test_sealed_speakers_and_rows_disjoint(self):
        old = experiment.csv_rows(experiment.OLD / "split-manifest.csv")
        fresh = experiment.csv_rows(experiment.PREFLIGHT / "sealed-test-manifest.csv")
        self.assertEqual(len(experiment.validate_training(old, fresh)), 386)
        for key in ("source_asset_id", "speaker_id", "audio_sha256", "decoded_pcm_sha256"):
            changed = [dict(r) for r in fresh]
            changed[0][key] = old[0][key]
            with self.assertRaisesRegex(ValueError, "overlaps"):
                experiment.validate_training(old, changed)
        changed = [dict(r) for r in old]
        next(r for r in changed if r["partition"] == "validation")["partition"] = "train"
        with self.assertRaises(ValueError):
            experiment.validate_training(changed, fresh)

    def test_seal_failure_blocks_model_access_and_receipt(self):
        with (
            patch.object(experiment, "verify_seal", side_effect=ValueError("bad seal")),
            patch.object(experiment, "extract_pairs") as extract,
            patch.object(experiment, "require_lock") as lock,
            patch.object(experiment, "exclusive_json") as write,
        ):
            for stage in ("fresh", "stress"):
                with self.assertRaisesRegex(ValueError, "bad seal"):
                    experiment.run_panel(stage)
            extract.assert_not_called()
            lock.assert_not_called()
            write.assert_not_called()

    def test_no_lock_means_no_fresh_extraction(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(experiment, "OUTPUT", Path(directory)),
            patch.object(experiment, "prerequisites", return_value=([], [], {}, {})),
            patch.object(experiment, "extract_pairs") as extract,
        ):
            with self.assertRaises(FileNotFoundError):
                experiment.run_panel("fresh")
            extract.assert_not_called()
            self.assertFalse((Path(directory) / "fresh-test-opened.json").exists())

    def test_opening_receipt_precedes_extraction_and_refuses_repeat(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(experiment, "OUTPUT", Path(directory)),
            patch.object(experiment, "prerequisites", return_value=([], [{"id": "1"}], {}, {})),
            patch.object(experiment, "require_lock", return_value={"encoder": {}}),
        ):
            output = Path(directory)
            (output / "lock.json").write_text("{}")

            def stopped(*_):
                self.assertTrue((output / "fresh-test-opened.json").exists())
                raise RuntimeError("synthetic extraction stop")

            with patch.object(experiment, "extract_pairs", side_effect=stopped) as extract:
                with self.assertRaisesRegex(RuntimeError, "synthetic extraction stop"):
                    experiment.run_panel("fresh")
                with self.assertRaises(FileExistsError):
                    experiment.run_panel("fresh")
                self.assertEqual(extract.call_count, 1)

    def test_stress_requires_fresh_completion(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(experiment, "OUTPUT", Path(directory)),
            patch.object(experiment, "prerequisites", return_value=([], [], {}, {})),
            patch.object(experiment, "require_lock", return_value={}),
            patch.object(experiment, "extract_pairs") as extract,
        ):
            with self.assertRaises(FileNotFoundError):
                experiment.run_panel("stress")
            extract.assert_not_called()

    def test_lock_detects_changed_code(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "lock.json").write_text(json.dumps({"source_code_sha256": {"old": "hash"}}))
            with (
                patch.object(experiment, "OUTPUT", output),
                self.assertRaisesRegex(ValueError, "Locked implementation"),
            ):
                experiment.require_lock({})

    def test_identical_prediction_ids_counts_and_paired_counts(self):
        rows = [
            dict(
                source_asset_id=str(i),
                speaker_id="s",
                speaker_name="synthetic",
                text="x",
                pinyin="x",
                tone=i + 1,
            )
            for i in range(4)
        ]
        features = {
            "asset_ids": np.array([str(i) for i in range(4)]),
            "A": np.zeros((4, 768)),
            "B": np.zeros((4, 2304)),
        }
        predictions = {"A": np.eye(4)[[0, 1, 0, 0]], "B": np.eye(4)[[0, 0, 2, 0]]}
        with patch.object(experiment, "predict_head", side_effect=lambda p, _: predictions[p]):
            report, records = experiment.evaluate(rows, features, {a: a for a in "AB"})
            self.assertEqual(len(records), 4)
            self.assertEqual([r["source_asset_id"] for r in records], list(features["asset_ids"]))
            self.assertEqual(report["A"]["n"], report["B"]["n"])
            self.assertEqual(
                report["paired_correctness"],
                dict(both_correct=1, A_only_correct=1, B_only_correct=1, both_wrong=1),
            )
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "predictions.csv"
                experiment.exclusive_csv(path, records)
                self.assertEqual(len(experiment.csv_rows(path)), 4)
            features["asset_ids"] = features["asset_ids"][::-1]
            with self.assertRaisesRegex(ValueError, "membership"):
                experiment.evaluate(rows, features, {a: a for a in "AB"})

    def test_missing_tone_balanced_accuracy_undefined(self):
        result = experiment.detailed_metrics([dict(tone=3)], [4])
        self.assertIsNone(result["balanced_accuracy"])
        self.assertEqual(result["directed_confusions"]["T3->T4"], dict(count=1, rate=1))


if __name__ == "__main__":
    unittest.main()

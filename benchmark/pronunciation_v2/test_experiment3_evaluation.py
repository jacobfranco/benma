"""Synthetic runner fixtures only. Never invoke evaluate or load the sealed panel into a model."""

import ast
import copy
import csv
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
import zlib
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

import evaluate_experiment3 as runner
import experiment3_metrics as m
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)


def fixture(sizes=(1, 3, 2), speakers=None):
    rows, a, b = [], [], []
    for s, size in enumerate(sizes):
        for tone in m.TONES:
            for j in range(size):
                rows.append(
                    {
                        "source_asset_id": f"synthetic:{s}:{tone}:{j}",
                        "speaker_id": speakers[s] if speakers else f"synthetic-speaker:{s}",
                        "speaker_native_status": "LEARNER" if s % 3 == 0 else "NATIVE",
                        "text": f"fixture-{tone}",
                        "pinyin": f"fixture{tone}",
                        "tone": str(tone),
                    }
                )
                a.append(tone if (s + j) % 2 else tone % 4 + 1)
                b.append(tone if (s + j) % 3 else (tone + 1) % 4 + 1)
    records = m.prediction_records(
        rows,
        [r["source_asset_id"] for r in rows],
        np.eye(4)[np.array(a) - 1],
        np.eye(4)[np.array(b) - 1],
    )
    return rows, records


class MetricsTests(unittest.TestCase):
    def test_metrics_against_independent_sklearn_oracle(self):
        rng = np.random.default_rng(51)
        y = np.tile([1, 2, 3, 4], 25)
        p = rng.integers(1, 5, size=len(y))
        result = m.numeric(m.exact_metrics(m.confusion(y, p)))
        self.assertEqual(
            result["confusion_matrix"], confusion_matrix(y, p, labels=m.TONES).tolist()
        )
        self.assertEqual(result["correct_count"], int((y == p).sum()))
        self.assertEqual(result["accuracy"], accuracy_score(y, p))
        self.assertAlmostEqual(result["balanced_accuracy"], balanced_accuracy_score(y, p))
        self.assertAlmostEqual(result["macro_f1"], f1_score(y, p, average="macro"))
        expected = precision_recall_fscore_support(y, p, labels=m.TONES, zero_division=0)
        for i, t in enumerate(map(str, m.TONES)):
            for k, values in zip(("precision", "recall", "f1", "support"), expected, strict=True):
                self.assertAlmostEqual(result["per_tone"][t][k], values[i])
        for a, b in ((2, 3), (3, 2), (3, 4), (4, 3)):
            d = result["directed_confusions"][f"T{a}->T{b}"]
            count = int(((y == a) & (p == b)).sum())
            self.assertEqual(d, {"count": count, "denominator": 25, "rate": count / 25})

    def test_zero_precision_and_missing_tone_ba(self):
        result = m.exact_metrics(m.confusion([1, 2], [1, 1]))
        self.assertIsNone(result["balanced_accuracy"])
        self.assertIsNone(result["per_tone"]["3"]["recall"])
        self.assertEqual(result["per_tone"]["3"]["f1"], 0)
        self.assertEqual(result["per_tone"]["2"]["precision"], 0)
        self.assertEqual(result["macro_f1"], Fraction(1, 6))

    def test_equal_speaker_is_unweighted_and_differences_are_paired(self):
        rows, records = fixture((1, 5))
        result = m.report(rows, records)
        for arm in ("A", "B"):
            speakers = result["per_speaker"].values()
            expected = sum(s[arm]["balanced_accuracy"] for s in speakers) / 2
            self.assertEqual(
                result["primary"][arm]["equal_speaker_mean_balanced_accuracy"], expected
            )
            self.assertNotEqual(expected, result["primary"][arm]["balanced_accuracy"])
        primary = result["primary"]
        for k in m.BOOT_METRICS:
            self.assertAlmostEqual(
                primary["difference_B_minus_A"][k], primary["B"][k] - primary["A"][k]
            )
        for s in result["per_speaker"].values():
            self.assertAlmostEqual(
                s["difference_B_minus_A"]["balanced_accuracy"],
                s["B"]["balanced_accuracy"] - s["A"]["balanced_accuracy"],
            )
        for t in map(str, m.TONES):
            for k in ("precision", "recall", "f1"):
                self.assertAlmostEqual(
                    primary["difference_B_minus_A"]["per_tone"][t][k],
                    primary["B"]["per_tone"][t][k] - primary["A"]["per_tone"][t][k],
                )

    def test_paired_categories(self):
        rows, _ = fixture((1,))
        records = m.prediction_records(
            rows,
            [r["source_asset_id"] for r in rows],
            np.eye(4)[[0, 1, 0, 0]],
            np.eye(4)[[0, 0, 2, 0]],
        )
        result = m.report(rows, records)
        self.assertEqual(
            result["primary"]["paired_correctness"],
            dict.fromkeys(("both_correct", "A_only_correct", "B_only_correct", "both_wrong"), 1),
        )

    def test_subgroups_are_secondary_and_cannot_drive_decision(self):
        rows, records = fixture()
        result = m.report(rows, records)
        for status, subgroup in result["source_declared_status_subgroups"].items():
            selected = [r for r in records if r["source_declared_speaker_status"] == status]
            self.assertEqual(subgroup["role"], "SECONDARY_DESCRIPTIVE")
            self.assertEqual(subgroup["A"]["support"], len(selected))
            self.assertEqual(subgroup["A"], m.numeric(m.pair_summary(selected)["A"]))
        for row, record in zip(rows, records, strict=True):
            row["speaker_native_status"] = record["source_declared_speaker_status"] = "NATIVE"
        self.assertEqual(result["decision"], m.report(rows, records)["decision"])

    def test_invalid_labels(self):
        for truth, prediction in [([1], [5]), ([1.5], [1]), ([1], [1, 2]), ([], [])]:
            with self.assertRaises(ValueError):
                m.confusion(truth, prediction)


class DecisionTests(unittest.TestCase):
    def inputs(self):
        a = m.exact_metrics(np.full((4, 4), 5, dtype=int))
        b = copy.deepcopy(a)
        a["equal_speaker_mean_balanced_accuracy"] = b["equal_speaker_mean_balanced_accuracy"] = (
            Fraction(1, 4)
        )
        speakers = {"fixture": {"A": copy.deepcopy(a), "B": copy.deepcopy(b)}}
        b["accuracy"] += Fraction(1, 100)
        return a, b, speakers

    def test_all_nine_conditions_and_ceiling_tie(self):
        a, b, s = self.inputs()
        self.assertTrue(m.decision(a, b, s)["promising"])
        self.assertEqual(len(m.decision(a, b, s)["checks"]), 9)
        b["accuracy"] = a["accuracy"]
        self.assertEqual(m.decision(a, b, s)["failed_conditions"], ["strict_pooled_improvement"])
        perfect = m.exact_metrics(np.eye(4, dtype=int) * 10)
        perfect["equal_speaker_mean_balanced_accuracy"] = Fraction(1)
        self.assertFalse(
            m.decision(perfect, perfect, {"s": {"A": perfect, "B": perfect}})["promising"]
        )

    def test_each_pooled_and_equal_speaker_regression_fails(self):
        for k in m.BOOT_METRICS:
            a, b, s = self.inputs()
            b[k] = a[k] - Fraction(1, 1000000)
            result = m.decision(a, b, s)
            self.assertFalse(result["promising"])
            key = (
                f"pooled_{k}_non_regression"
                if k in m.POOLED
                else "equal_speaker_mean_ba_non_regression"
            )
            self.assertIn(key, result["failed_conditions"])

    def test_tone_thresholds_exact_and_strictly_above(self):
        for tone in map(str, m.TONES):
            for k in ("precision", "recall", "f1"):
                for drop, allowed in (
                    (Fraction(1, 20), True),
                    (Fraction(1, 20) + Fraction(1, 10**15), False),
                ):
                    a, b, s = self.inputs()
                    b["per_tone"][tone][k] = a["per_tone"][tone][k] - drop
                    result = m.decision(a, b, s)
                    self.assertEqual(result["promising"], allowed)
                    if not allowed:
                        self.assertIn(f"tone_{k}_drop_at_most_0.05", result["failed_conditions"])
                        self.assertEqual(
                            result["checks"][("precision", "recall", "f1").index(k) + 5]["details"][
                                "violations"
                            ],
                            {tone: drop},
                        )

    def test_speaker_threshold_exact_and_strictly_above(self):
        for drop, allowed in (
            (Fraction(1, 10), True),
            (Fraction(1, 10) + Fraction(1, 10**15), False),
        ):
            a, b, s = self.inputs()
            s["fixture"]["B"]["balanced_accuracy"] -= drop
            result = m.decision(a, b, s)
            self.assertEqual(result["promising"], allowed)
            if not allowed:
                self.assertEqual(result["failed_conditions"], ["speaker_ba_drop_at_most_0.10"])

    def test_rational_real_counts_allow_exact_tone_drop(self):
        a = m.exact_metrics(np.eye(4, dtype=int) * 20)
        cm = np.eye(4, dtype=int) * 19
        for i in range(4):
            cm[i, (i + 1) % 4] = 1
        b = m.exact_metrics(cm)
        a["equal_speaker_mean_balanced_accuracy"] = a["balanced_accuracy"]
        b["equal_speaker_mean_balanced_accuracy"] = b["balanced_accuracy"]
        result = m.decision(a, b, {"s": {"A": a, "B": b}})
        self.assertTrue(all(c["passed"] for c in result["checks"][5:]))


class IdentityBootstrapTests(unittest.TestCase):
    def test_identity_order_missing_duplicate_and_mutation_rejected(self):
        rows, records = fixture()
        variants = [records[::-1], records[:-1], [records[0], *records[1:-1], records[0]]]
        for key in m.IDENTITY:
            changed = copy.deepcopy(records)
            changed[0][key] = "changed"
            variants.append(changed)
        for changed in variants:
            with self.assertRaises(ValueError):
                m.validate_records(rows, changed)
        with self.assertRaises(ValueError):
            m.prediction_records(
                rows,
                [r["source_asset_id"] for r in rows][::-1],
                np.ones((len(rows), 4)) / 4,
                np.ones((len(rows), 4)) / 4,
            )

    def test_probabilities_and_correctness_rejected(self):
        rows, records = fixture()
        for key, value in (
            ("A_T1_probability", float("nan")),
            ("A_T1_probability", 1.1),
            ("A_prediction", 5),
            ("A_correct", 3),
        ):
            changed = copy.deepcopy(records)
            changed[0][key] = value
            with self.assertRaises(ValueError):
                m.validate_records(rows, changed)
        p = np.ones((len(rows), 4)) / 4
        records = m.prediction_records(rows, [r["source_asset_id"] for r in rows], p, p)
        self.assertTrue(all(r["A_prediction"] == 1 for r in records))
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=m.COLUMNS)
        writer.writeheader()
        writer.writerows(records)
        m.validate_records(rows, list(csv.DictReader(io.StringIO(stream.getvalue()))))

    def test_bootstrap_reproducible_and_explicit_speaker_copy_oracle(self):
        rows, records = fixture((1, 5, 2))
        first = m.bootstrap(rows, records)
        self.assertEqual(first, m.bootstrap(rows, records))
        self.assertEqual(first["configuration"], m.BOOTSTRAP)
        draws = np.random.default_rng(20261002).integers(0, 3, size=(10000, 3))
        self.assertEqual(first["sampled_speaker_indices"], draws.tolist())
        self.assertTrue(any(len(set(draw)) < 3 for draw in draws))
        for i, draw in enumerate(draws[:75]):
            copied = []
            bas = {"A": [], "B": []}
            for index in draw:
                group = [r for r in records if r["speaker_id"] == first["speaker_order"][index]]
                copied.extend(group)
                for arm in bas:
                    bas[arm].append(m.pair_summary(group)[arm]["balanced_accuracy"])
            direct = m.pair_summary(copied)
            for k in m.POOLED:
                self.assertAlmostEqual(
                    first["differences"][k][i], float(direct["B"][k] - direct["A"][k])
                )
            self.assertAlmostEqual(
                first["differences"][m.BOOT_METRICS[-1]][i],
                float((sum(bas["B"]) - sum(bas["A"])) / 3),
            )
        for k, v in first["differences"].items():
            self.assertEqual(
                first["intervals_95_percent"][k],
                np.percentile(v, [2.5, 97.5], method="linear").tolist(),
            )
        same = m.prediction_records(
            rows,
            [r["source_asset_id"] for r in rows],
            np.ones((len(rows), 4)) / 4,
            np.ones((len(rows), 4)) / 4,
        )
        self.assertTrue(
            all(set(v) == {0.0} for v in m.bootstrap(rows, same)["differences"].values())
        )


class GateTests(unittest.TestCase):
    def test_import_and_verify_have_no_model_imports(self):
        command = (
            "import sys; import evaluate_experiment3; assert 'torch' not in sys.modules; "
            "assert 'transformers' not in sys.modules; assert 'features' not in sys.modules"
        )
        subprocess.run([sys.executable, "-c", command], cwd=runner.CODE, check=True)
        tree = ast.parse(Path(runner.__file__).read_text())
        evaluate = next(
            n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "evaluate"
        )
        self.assertIsInstance(evaluate.body[0], ast.Assign)
        self.assertEqual(evaluate.body[0].value.func.id, "verify")
        self.assertTrue(evaluate.body[0].value.keywords[0].value.value)

    def test_lock_digest_and_every_state_component_fail_closed(self):
        keys = [
            "manifest_sha256",
            "seal_sha256",
            "frozen_sha256",
            "encoder",
            "preprocessing",
            "source_sha256",
            "environment",
            "output_schema_sha256",
            "metric_definitions",
            "bootstrap",
            "promising_rule",
        ]
        state = dict.fromkeys(keys, "original")
        with tempfile.TemporaryDirectory() as temp, patch.object(runner, "OUT", Path(temp)):
            path = Path(temp) / "runner.lock.json"
            runner.exclusive(
                path, runner.encoded({"frozen_state": state, "test_predictions_opened": False})
            )
            sha = runner.digest(path)
            runner.require_runner_lock(sha, state)
            for key in keys:
                with self.assertRaises(ValueError, msg=key):
                    runner.require_runner_lock(sha, {**state, key: "changed"})
            for invalid in (None, "0" * 64):
                with self.assertRaises(ValueError):
                    runner.require_runner_lock(invalid, state)
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaises(ValueError):
                runner.require_runner_lock(sha, state)

    def test_missing_lock_and_opened_claim_block_before_pcm(self):
        with (
            tempfile.TemporaryDirectory() as temp,
            patch.object(runner, "OUT", Path(temp)),
            patch.object(runner, "frozen_state", return_value={}),
            patch.object(runner, "verify_audio", side_effect=AssertionError("PCM reached")),
        ):
            with self.assertRaises((ValueError, FileNotFoundError)):
                runner.verify("0" * 64, require_lock=True)
            (Path(temp) / "opened").mkdir()
            with self.assertRaises(FileExistsError):
                runner.verify("0" * 64, require_lock=True)

    def test_exclusive_files_and_lock_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(runner, "OUT", Path(temp)):
            path = Path(temp) / "runner.lock.json"
            runner.exclusive(path, b"original")
            with self.assertRaises(FileExistsError):
                runner.exclusive(path, b"changed")
            with self.assertRaises(FileExistsError):
                runner.lock()
            self.assertEqual(path.read_bytes(), b"original")

    def test_hash_mutation_and_missing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input"
            path.write_bytes(b"frozen")
            sha = runner.digest(path)
            runner.require_hash(path, sha)
            path.write_bytes(b"changed")
            with self.assertRaises(ValueError):
                runner.require_hash(path, sha)
            path.unlink()
            with self.assertRaises(FileNotFoundError):
                runner.require_hash(path, sha)

    def test_source_and_pcm_verification_tamper(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "fake.wav"
            raw = b"synthetic file bytes"
            path.write_bytes(raw)
            pcm = np.zeros(800, dtype="<f4").tobytes()
            row = dict(
                local_path=str(path),
                source_asset_id="fixture",
                audio_sha256=hashlib.sha256(raw).hexdigest(),
                source_sha256=hashlib.sha256(raw).hexdigest(),
                source_sha1=hashlib.sha1(raw).hexdigest(),
                archive_crc32=str(zlib.crc32(raw)),
                source_bytes=str(len(raw)),
                sample_rate_hz="16000",
                channels="1",
                duration_seconds="0.05",
                decoded_pcm_sha256=hashlib.sha256(b"16000:1:f32le:" + pcm).hexdigest(),
                evaluation_pcm_sha256=hashlib.sha256(pcm).hexdigest(),
            )
            probe = json.dumps(
                {"streams": [{"codec_type": "audio", "sample_rate": "16000", "channels": 1}]}
            ).encode()

            def check(candidate):
                with (
                    patch.object(runner.subprocess, "check_output", side_effect=[probe, pcm]),
                    patch.object(runner.panel, "mono16_pcm", return_value=pcm),
                ):
                    runner.verify_audio(candidate)

            check(row)
            for k in (
                "audio_sha256",
                "source_sha256",
                "source_sha1",
                "decoded_pcm_sha256",
                "evaluation_pcm_sha256",
                "archive_crc32",
                "source_bytes",
                "sample_rate_hz",
                "channels",
                "duration_seconds",
            ):
                with self.assertRaises(ValueError, msg=k):
                    check({**row, k: "0"})
            path.unlink()
            with self.assertRaises(FileNotFoundError):
                check(row)

    def test_exact_composition_synthetic(self):
        rows = []
        for s in runner.SPEAKERS:
            name = s.split(":")[1]
            for t in m.TONES:
                for j in range(10):
                    rows.append(
                        dict(
                            speaker_id=s,
                            speaker_name=name,
                            speaker_native_status="LEARNER" if name.startswith("L_") else "NATIVE",
                            tone=str(t),
                            source_asset_id=f"fake:{s}:{t}:{j}",
                        )
                    )
        runner.verify_composition(rows)
        for key in ("speaker_id", "tone", "speaker_native_status", "source_asset_id"):
            changed = copy.deepcopy(rows)
            changed[0][key] = rows[-1][key]
            if key == "speaker_native_status":
                changed[0][key] = "LEARNER"
            with self.assertRaises(ValueError):
                runner.verify_composition(changed)
        with self.assertRaises(ValueError):
            runner.verify_composition(rows[:-1])


class OutputTests(unittest.TestCase):
    def test_future_inference_boundary_with_synthetic_waveforms_only(self):
        import features
        import model_probe
        import torch
        import transformers

        rows, _ = fixture((1,))
        wave = np.zeros(800, dtype="<f4")
        raw = b"synthetic audio placeholder; decoder is mocked"
        model = torch.nn.Linear(1, 1)
        processor = object()
        collected = []

        def encode(encoder, feature_processor, waves, *, layers):
            self.assertIs(encoder, model)
            self.assertIs(feature_processor, processor)
            self.assertFalse(encoder.training)
            self.assertTrue(all(not p.requires_grad for p in encoder.parameters()))
            self.assertTrue(all(p.device.type == "cpu" for p in encoder.parameters()))
            self.assertTrue(all(p.dtype == torch.float32 for p in encoder.parameters()))
            self.assertEqual(layers, (8,))
            self.assertEqual(len(waves), 1)
            np.testing.assert_array_equal(waves[0], wave)
            collected.append(len(waves[0]))
            return {8: np.zeros((1, 768), dtype=np.float32)}

        def probability(*args):
            x = args[-1]
            self.assertEqual(x.shape, (4, 768))
            return np.eye(4)

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "fixture.wav"
            path.write_bytes(raw)
            for row in rows:
                row.update(
                    local_path=str(path),
                    audio_sha256=hashlib.sha256(raw).hexdigest(),
                    evaluation_pcm_sha256=hashlib.sha256(wave.tobytes()).hexdigest(),
                )
            with (
                patch.object(
                    transformers.Wav2Vec2Model,
                    "from_pretrained",
                    return_value=(
                        model,
                        {"missing_keys": [], "mismatched_keys": [], "error_msgs": []},
                    ),
                ) as loader,
                patch.object(
                    transformers.Wav2Vec2FeatureExtractor, "from_pretrained", return_value=processor
                ),
                patch.object(features, "load_waveform", return_value=wave),
                patch.object(features, "encode_waveforms", side_effect=encode),
                patch.object(model_probe, "predict_head", side_effect=probability),
                patch.object(runner, "nonlinear_probabilities", side_effect=probability),
            ):
                records = runner.infer(rows, {"encoder": {"snapshot": "synthetic-only"}})
                self.assertEqual(loader.call_args.args, ("synthetic-only",))
                self.assertTrue(loader.call_args.kwargs["local_files_only"])
                self.assertEqual(loader.call_args.kwargs["attn_implementation"], "eager")
                self.assertEqual(loader.call_args.kwargs["torch_dtype"], torch.float32)
        self.assertEqual(collected, [800] * 4)
        m.validate_records(rows, records)

    def test_full_synthetic_schemas_review_and_csv(self):
        rows, records = fixture((10,) * 18, runner.SPEAKERS)
        results = m.report(rows, records)
        boot = m.bootstrap(rows, records)
        for name, value in (
            ("predictions.csv", records),
            ("results.json", results),
            ("bootstrap.json", boot),
        ):
            runner.validate_output(name, value)
        review = runner.review(results, boot)
        self.assertIn("ALL 720", review)
        self.assertIn("not population guarantees", review)
        self.assertIn("NATIVE", review)
        for key in results["decision"]["failed_conditions"]:
            self.assertIn(key, review)
        for name, value in (("results.json", results), ("bootstrap.json", boot)):
            changed = copy.deepcopy(value)
            changed["extra"] = 1
            with self.assertRaises(ValueError):
                runner.validate_output(name, changed)
        spec = runner.read_json(runner.SCHEMA)
        self.assertEqual(spec["csv"]["columns"], m.COLUMNS)
        receipt = dict(
            schema_version=m.VERSION,
            completed_at="synthetic",
            status="COMPLETE",
            runner_lock_sha256="synthetic",
            manifest_sha256=runner.MANIFEST_SHA,
            rows=720,
            speakers=18,
            test_predictions_opened=True,
            artifacts_sha256=dict.fromkeys(
                (
                    "opening-receipt.json",
                    "predictions.csv",
                    "results.json",
                    "bootstrap.json",
                    "review.md",
                ),
                "synthetic",
            ),
        )
        runner.validate_output("evaluation-receipt.json", receipt)

    def test_nonlinear_inference_standardization_matches_frozen_training_policy(self):
        # Synthetic arrays/embeddings only; no frozen head or sealed audio is read.
        import torch
        from sklearn.preprocessing import StandardScaler

        rng = np.random.default_rng(713)
        x = rng.normal(size=(7, 768)).astype(np.float32)
        scaler = StandardScaler().fit(rng.normal(size=(13, 768)).astype(np.float32))
        arrays = {
            "mean": scaler.mean_,
            "scale": scaler.scale_,
            "0.weight": rng.normal(size=(8, 768)).astype(np.float32),
            "0.bias": rng.normal(size=8).astype(np.float32),
            "2.weight": rng.normal(size=(4, 8)).astype(np.float32),
            "2.bias": rng.normal(size=4).astype(np.float32),
        }
        with tempfile.TemporaryDirectory() as temp, patch.object(runner, "FROZEN", Path(temp)):
            np.savez(Path(temp) / "head-nonlinear.npz", **arrays)
            actual = runner.nonlinear_probabilities(x)
        v = torch.from_numpy(scaler.transform(x))
        with torch.inference_mode():
            hidden = torch.tanh(
                torch.nn.functional.linear(
                    v, torch.from_numpy(arrays["0.weight"]), torch.from_numpy(arrays["0.bias"])
                )
            )
            logits = torch.nn.functional.linear(
                hidden, torch.from_numpy(arrays["2.weight"]), torch.from_numpy(arrays["2.bias"])
            )
            expected = torch.softmax(logits, dim=1).numpy()
        np.testing.assert_array_equal(actual, expected)


if __name__ == "__main__":
    unittest.main()

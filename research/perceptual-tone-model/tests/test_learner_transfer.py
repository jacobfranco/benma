"""Inference guards, label isolation, descriptive metrics, and sealed reproduction."""

import ast
import copy
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from perceptual_tone import learner_transfer as transfer
from perceptual_tone.common import read_json, read_rows
from perceptual_tone.learner_release import RELEASE, RUN, verify_release


class LearnerTransferTests(unittest.TestCase):
    def test_release_attestation_raw_notes_and_provenance_are_frozen(self):
        verify_release()
        acceptance = read_json(RELEASE / "review-acceptance.json")
        self.assertTrue(acceptance["accepted_by_developer_attestation"])
        self.assertFalse(acceptance["playback_telemetry_complete"])
        raw = {r["unit_id"]: r for r in read_json(RELEASE / "raw-draft.json")["reviews"]}
        units = read_rows(RELEASE / "all-units.jsonl")
        self.assertTrue(all(r["qa"] == raw[r["example_id"]] for r in units))
        self.assertTrue(all(not r["eligible_for_training"] for r in units))
        self.assertTrue(all(r["actual_realized_acoustic_tone"] == "UNKNOWN" for r in units))

    def test_encoder_contract_excludes_labels_and_qa(self):
        unit = read_rows(RELEASE / "primary.jsonl")[0]
        before = transfer.contract(unit)
        changed = copy.deepcopy(unit)
        for key in (
            "hanzi",
            "alignment_pinyin",
            "expected_surface_tone",
            "intended_lexical_tone",
            "qa",
        ):
            changed[key] = "MUTATED LABEL"
        self.assertEqual(before, transfer.contract(changed))
        self.assertEqual(
            set(before), {"audio_reference", "audio_sha256", "read_unit", "pooling", "context"}
        )

    def test_descriptive_denominators_neutral_unknown_abstentions(self):
        rows = read_rows(RUN / "primary/predictions.jsonl")
        summary = transfer.summary(rows)
        self.assertEqual(summary["interpretation"], "DESCRIPTIVE")
        expanded = summary["models"]["expanded"]
        self.assertEqual(expanded["intended_lexical_tone_agreement"]["resolved_numbered_n"], 15)
        surface = expanded["expected_surface_tone_agreement"]
        self.assertEqual(
            (
                surface["resolved_numbered_n"],
                surface["neutral_excluded"],
                surface["unresolved_excluded"],
            ),
            (10, 1, 5),
        )
        self.assertEqual(summary["models"]["deterministic"]["abstentions"], 14)
        self.assertNotIn("accuracy", str(summary).lower())
        self.assertEqual(summary["model_agreement"]["expanded_vs_pilot"]["jointly_covered"], 16)

    def test_models_reload_without_any_fit_and_reproduce_primary_probabilities(self):
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline

        transfer.check_phase("primary")
        with (
            patch.object(Pipeline, "fit", side_effect=AssertionError("learner fit forbidden")),
            patch.object(
                LogisticRegression, "fit", side_effect=AssertionError("learner fit forbidden")
            ),
        ):
            models = transfer.load_models(read_json(RELEASE / "inference-config.json"))
            matrix = np.load(RUN / "primary/features.npy", allow_pickle=False)
            actual = transfer.probabilities(models, matrix)
        rows = read_rows(RUN / "primary/predictions.jsonl")
        for name, values in actual.items():
            np.testing.assert_allclose(
                values, [r[name]["probabilities"] for r in rows], atol=1e-12, rtol=0
            )

    def test_no_training_adaptation_or_metric_selection_calls(self):
        tree = ast.parse(Path(transfer.__file__).read_text())
        calls = {
            n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id
            for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, (ast.Attribute, ast.Name))
        }
        self.assertFalse(
            {"fit", "partial_fit", "backward", "pipeline", "GridSearchCV", "metric"} & calls
        )
        with (
            patch.object(transfer, "verify_release", side_effect=ValueError("unsealed")),
            self.assertRaisesRegex(ValueError, "unsealed"),
        ):
            transfer.infer("primary")

    def test_supplemental_cannot_precede_primary_freeze(self):
        with (
            patch.object(transfer, "check_phase", side_effect=ValueError("primary not frozen")),
            self.assertRaisesRegex(ValueError, "primary not frozen"),
        ):
            transfer.infer("unknown")

    def test_all_frozen_inference_schemas_and_quarantine_population(self):
        for phase in ("primary", "diagnostic", "unknown"):
            transfer.check_phase(phase)
            rows = read_rows(RUN / phase / "predictions.jsonl")
            accepted = read_rows(RELEASE / (phase + ".jsonl"))
            self.assertEqual({r["example_id"] for r in rows}, {r["example_id"] for r in accepted})
            for row in rows:
                self.assertEqual(row["realized_tone"], "UNKNOWN")
                self.assertIn(row["expected_surface_tone"], (None, 1, 2, 3, 4, 5))
                for name in ("expanded", "pilot"):
                    item = row[name]
                    probabilities = np.asarray(item["probabilities"])
                    self.assertEqual(probabilities.shape, (4,))
                    self.assertTrue(np.isfinite(probabilities).all())
                    self.assertAlmostEqual(float(probabilities.sum()), 1.0)
                    self.assertEqual(item["prediction"], transfer.CLASSES[probabilities.argmax()])
                    self.assertEqual(item["confidence"], float(probabilities.max()))
                self.assertIn(row["deterministic"]["prediction"], (None, *transfer.CLASSES))


if __name__ == "__main__":
    unittest.main()

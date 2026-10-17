import sys
import unittest

from perceptual_tone.common import PACKAGE

sys.path.insert(0, str(PACKAGE / "scripts"))
from aishell3_finalize import confidence_audit


class FinalizationTests(unittest.TestCase):
    def test_confidence_boundary_counts_and_error_identities(self):
        rows = [
            {"example_id": "low", "truth": "T1", "prediction": "T1", "probabilities": [0.25] * 4},
            {
                "example_id": "edge",
                "truth": "T3",
                "prediction": "T4",
                "probabilities": [0.05, 0.05, 0.1, 0.8],
            },
            {
                "example_id": "high",
                "truth": "T3",
                "prediction": "T3",
                "probabilities": [0, 0, 0.9, 0.1],
            },
            {"example_id": "one", "truth": "T4", "prediction": "T1", "probabilities": [1, 0, 0, 0]},
        ]
        result = confidence_audit(rows)
        self.assertEqual(sum(b["correct"] for b in result["bins"]), 2)
        self.assertEqual(sum(b["incorrect"] for b in result["bins"]), 2)
        self.assertEqual(result["bins"][-1]["n"], 2)
        self.assertEqual(result["bins"][-2]["n"], 1)
        self.assertEqual(
            [r["example_id"] for r in result["high_confidence_errors"]], ["edge", "one"]
        )

    def test_histogram_refuses_unaccounted_probability(self):
        with self.assertRaisesRegex(ValueError, "does_not_cover"):
            confidence_audit(
                [{"truth": "T1", "prediction": "T1", "probabilities": [float("nan")] * 4}]
            )

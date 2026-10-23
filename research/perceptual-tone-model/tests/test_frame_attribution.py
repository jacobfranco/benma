"""Focused research checks against persisted frames; never run the encoder or fit."""

import copy
import unittest

import numpy as np
from perceptual_tone.common import PACKAGE, file_hash, read_json
from perceptual_tone.frame_attribution import (
    CASES,
    OUT,
    affine_head,
    decompose,
    evaluate,
    frame_scores,
    geometry,
    positional_plan,
    verify_freeze,
)
from perceptual_tone.learner_transfer import load_models


class FrameAttributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = read_json(OUT / "results.json")
        cls.lock = read_json(PACKAGE / "configs/dev-learned-lock.json")
        cls.models = load_models(cls.lock["model_method"])

    def test_exact_four_case_scope(self):
        self.assertEqual([(c["recording"], c["index"]) for c in self.results["cases"]], list(CASES))

    def test_exact_frame_reconstruction(self):
        expected = [
            ([20, 21, 22], list(range(13, 24))),
            (list(range(19, 24)), list(range(13, 24))),
            (list(range(18, 29)), list(range(13, 30))),
            (list(range(13, 29)), list(range(13, 36))),
        ]
        for case, (current, new) in zip(self.results["cases"], expected, strict=True):
            for key, ids in (("current", current), ("new", new)):
                centers, actual = geometry(case[key + "_contract"])
                np.testing.assert_array_equal(actual, ids)
                np.testing.assert_array_equal(centers, case["centers"])
            self.assertEqual(case["plan"]["shared"], current)
            self.assertEqual(case["plan"]["removed"], [])

    def test_half_open_boundary(self):
        contract = copy.deepcopy(self.results["cases"][0]["new_contract"])
        # Centers occur at half samples; nearest-sample boundary falls below/above them.
        contract["pooling"] = [2.02000, 2.04000]
        _, ids = geometry(contract)
        self.assertEqual(ids.tolist(), [14])

    def test_contributions_reproduce_all_subset_logits(self):
        for case in self.results["cases"]:
            hidden = np.load(OUT / case["case"] / "layer9.npy", allow_pickle=False)
            for head, data in case["heads"].items():
                scores, bias, raw, raw_bias = frame_scores(hidden, self.models[head])
                for sub in data["subsets"].values():
                    ids = sub["frames"]
                    np.testing.assert_allclose(
                        scores[ids].mean(0) + bias, sub["logits"], atol=1e-11, rtol=0
                    )
                    np.testing.assert_allclose(
                        raw[ids].mean(0) + raw_bias, sub["logits"], atol=1e-11, rtol=0
                    )

    def test_added_removed_shared_accounting(self):
        # Includes a removed-frame case absent from the four nested real spans.
        scores = np.arange(24, dtype=float).reshape(6, 4) ** 1.3
        d = decompose(scores, np.array([1.0, -2, 3, 4]), [0, 1, 2], [1, 2, 3, 4])
        np.testing.assert_allclose(
            d["delta"],
            np.array(d["added_direct"]) - d["removed_old"] + np.array(d["shared_dilution_delta"]),
        )

    def test_deterministic_regions_and_ablation(self):
        for case in self.results["cases"]:
            p = positional_plan(case["plan"]["current"], case["plan"]["new"])
            self.assertEqual(p, case["plan"])
            self.assertEqual(
                sorted(i for region in p["regions"].values() for i in region), p["new"]
            )
            hidden = np.load(OUT / case["case"] / "layer9.npy", allow_pickle=False)
            for head, data in case["heads"].items():
                pair = [int(t[1]) - 1 for t in data["pair"]]
                for name, ids in p["subsets"].items():
                    actual = evaluate(
                        hidden, ids, self.models[head], pair, np.array(case["centers"])
                    )
                    np.testing.assert_array_equal(
                        actual["probabilities"], data["subsets"][name]["probabilities"]
                    )

    def test_no_label_pitch_or_prediction_selection_inputs(self):
        import inspect

        self.assertEqual(list(inspect.signature(positional_plan).parameters), ["current", "new"])
        for case in self.results["cases"]:
            changed = copy.deepcopy(case)
            changed.update(
                character="different",
                expected_tone=99,
                lexical_target="unrelated",
                desired_answer="T4",
                grade=-1,
                heads={"expanded": "T1"},
                acoustics={},
            )
            for value in (case, changed):
                _, c = geometry(value["current_contract"])
                _, n = geometry(value["new_contract"])
                self.assertEqual(positional_plan(c, n), case["plan"])

    def test_nonfinite_embeddings_rejected(self):
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            frame_scores(np.full((1, 768), np.nan), self.models["expanded"])

    def test_pipeline_is_affine_for_finite_input(self):
        for model in self.models.values():
            mu, scale, _coef, bias, w = affine_head(model)
            x = np.linspace(-1, 1, 768)[None]
            np.testing.assert_allclose(
                model.decision_function(x), x @ w.T + bias - w @ mu, atol=1e-11, rtol=0
            )
            self.assertTrue(np.all(scale > 0))

    def test_frozen_integrity_and_cached_tensors(self):
        self.assertEqual(verify_freeze()["changed"], [])
        for case in self.results["cases"]:
            self.assertEqual(
                file_hash(OUT / case["case"] / "layer9.npy"), case["encoder"]["tensor_sha256"]
            )
        for spec in self.lock["model_method"]["models"].values():
            self.assertEqual(file_hash(spec["path"]), spec["sha256"])

    def test_original_outputs_reproduced(self):
        for case in self.results["cases"]:
            for data in case["heads"].values():
                for err in data["reproduction_errors"].values():
                    self.assertTrue(err["torch_pool_bitwise_matches_cache"])
                    self.assertLess(err["probability_max_abs"], 2e-6)


if __name__ == "__main__":
    unittest.main()

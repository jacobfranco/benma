"""Focused offline audit invariants; no encoder or classifier inference."""

import copy
import unittest

import numpy as np
from perceptual_tone.common import ROOT, digest, file_hash, read_json
from perceptual_tone.pooling_blocker_audit import (
    ARM,
    EVIDENCE,
    GATE,
    HEADS,
    OUT,
    PRIOR,
    RIGHT,
    independent_evidence,
    load_sealed,
    right_frame,
    select,
    selection_rows,
    weighted_decomposition,
)


class BlockerAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reps, cls.preds = load_sealed()
        cls.selection = read_json(OUT / "selection.json")
        cls.rows = selection_rows(cls.reps, cls.preds)
        cls.detail = read_json(OUT / "right-edge-contributions.json")

    def test_fixed_selection_and_order_independence(self):
        self.assertEqual(select(self.rows), self.selection)
        self.assertEqual(select(self.rows[::-1]), self.selection)
        self.assertEqual(len(self.selection["native_cases"]), 22)
        self.assertEqual(len(self.selection["native_controls"]), 22)
        self.assertEqual(len({r["control"] for r in self.selection["native_controls"]}), 22)

    def test_all_flips_and_top_ranked_cases_included(self):
        native = [r for r in self.rows if r["dataset"] == "native"]
        flips = {r["id"] for r in native if any(r[h + "_flip"] for h in HEADS)}
        self.assertEqual(len(flips), 21)
        self.assertLessEqual(flips, set(self.selection["native_cases"]))
        for key in ("expanded_tv", "pilot_tv", "removed_weight_share"):
            ids = {r["id"] for r in sorted(native, key=lambda r: (-r[key], r["id"]))[:3]}
            self.assertLessEqual(ids, set(self.selection["native_cases"]))

    def test_native_controls_stable_correct_and_disjoint(self):
        rows = {r["id"]: r for r in self.rows}
        for match in self.selection["native_controls"]:
            r = rows[match["control"]]
            self.assertNotIn(r["id"], self.selection["native_cases"])
            self.assertEqual(r["tone"], rows[match["case"]]["tone"])
            for h in HEADS:
                self.assertFalse(r[h + "_flip"])
                self.assertLessEqual(r[h + "_tv"], 0.02)
                self.assertEqual(r[h + "_prediction"], r["tone"])

    def test_exact_right_weight_and_unchanged_owner(self):
        for i in self.selection["native_cases"]:
            b, r = self.reps[i, ARM, "BASE"], self.reps[i, ARM, RIGHT]
            d = right_frame(b, r)
            self.assertEqual(b["ownership_span"], r["ownership_span"])
            self.assertEqual(d["removed_frame_id"], b["frame_ids"][-1])
            self.assertEqual(d["removed_weight_share"], b["normalized_weights"][-1])
            self.assertEqual(d["removed_raw_weight"], b["acoustic_audit"]["raw_weights"][-1])
            self.assertEqual(d["removed_rms"], b["acoustic_audit"]["rms_20ms"][-1])

    def test_exact_cached_score_reconstruction_both_heads_all_fixed_items(self):
        self.assertEqual(len(self.detail), 88)
        for r in self.detail:
            b = self.reps[r["id"], ARM, "BASE"]
            d = weighted_decomposition(
                r["frame_class_scores"], r["decomposition"]["bias"], b["normalized_weights"]
            )
            for key, state in (("before", "BASE"), ("after", RIGHT)):
                np.testing.assert_allclose(
                    d[key], self.preds[r["id"], ARM, state, r["head"]]["logits"], atol=2e-11, rtol=0
                )
            self.assertAlmostEqual(
                r["margin_after"] - r["margin_before"],
                -r["removed_margin_contribution"] + r["renormalization_margin_delta"],
                places=11,
            )
            for key in ("before", "after", "delta"):
                np.testing.assert_allclose(
                    d[key], r["raw_origin_decomposition"][key], atol=2e-11, rtol=0
                )

    def test_general_weighted_deletion_identity(self):
        rng = np.random.default_rng(928)
        for n in (4, 7, 20):
            scores, bias = rng.normal(size=(n, 4)), rng.normal(size=4)
            weights = rng.random(n)
            weights /= weights.sum()
            d = weighted_decomposition(scores, bias, weights)
            np.testing.assert_allclose(
                d["after"], weights[:-1] @ scores[:-1] / (1 - weights[-1]) + bias, atol=1e-12
            )
            np.testing.assert_allclose(
                d["delta"],
                -np.array(d["removed_contribution"]) + d["renormalization_delta"],
                atol=1e-12,
            )

    def test_complete_learner_disagreements_and_controls(self):
        expected = sorted(
            r["id"]
            for r in self.rows
            if r["dataset"] == "learner_primary"
            and r["expanded_prediction"] != r["pilot_prediction"]
        )
        self.assertEqual(expected, self.selection["learner_disagreements"])
        self.assertEqual(len(expected), 7)
        self.assertEqual(len(self.selection["learner_controls"]), 7)
        self.assertEqual(
            set(self.selection["learner_base_usable_ids"]) - set(expected),
            {r["control"] for r in self.selection["learner_controls"]},
        )

    def test_no_expected_tone_or_grade_selection_leakage(self):
        poison = copy.deepcopy(self.rows)
        for r in poison:
            r.update(
                expected_tone="T4",
                lexical_tone="T1",
                sandhi_expectation="T2",
                grade="wrong",
                jacob_realized_tone="T3",
                failed_solo_annotation="T4",
            )
            if r["dataset"] == "learner_primary":
                r["tone"] = "deliberately_wrong_learner_metadata"
        self.assertEqual(select(poison), self.selection)

    def test_independent_evidence_whitelist_and_no_failed_truth(self):
        raw = read_json(EVIDENCE / "raw.json")
        dt = {r["example_id"]: r for r in read_json(EVIDENCE / "output.json")}
        for r in raw:
            clean = independent_evidence(r, dt[r["example_id"]])
            poisoned, pd = copy.deepcopy(r), copy.deepcopy(dt[r["example_id"]])
            for row in (poisoned, pd):
                row.update(
                    expected_tone="T4",
                    lexical_tone="T2",
                    grade="correct",
                    jacob_realized_tone="T1",
                    failed_solo_annotation="T3",
                )
            self.assertEqual(clean, independent_evidence(poisoned, pd))
            self.assertFalse(clean["solo_annotation_used"])
            self.assertIsNone(clean["independent_listener_truth"])
        self.assertFalse(read_json(GATE)["confirmatory_model_evaluation_permitted"])

    def test_invalid_f0_cannot_be_promoted_by_deterministic_answer(self):
        raw = read_json(EVIDENCE / "raw.json")
        dt = {r["example_id"]: r for r in read_json(EVIDENCE / "output.json")}
        for r in raw:
            if r["example_id"] not in self.selection["learner_disagreements"]:
                continue
            pd = copy.deepcopy(dt[r["example_id"]])
            pd["prediction"] = "T4"
            pd["shape"]["familySafe"] = True
            e = independent_evidence(r, pd)
            self.assertIn(e["quality"], ("WEAK", "UNAVAILABLE"))
            self.assertIsNone(e["usable_family"])
        e = [r for r in read_json(OUT / "independent-evidence.json") if r["disagreement"]]
        self.assertEqual(sum(r["quality"] == "WEAK" for r in e), 5)
        self.assertEqual(sum(r["quality"] == "UNAVAILABLE" for r in e), 2)
        self.assertTrue(all(r["head_comparison"] == "unresolved" for r in e))

    def test_deterministic_summaries(self):
        summary = read_json(OUT / "cross-synthesis.json")
        source = {
            "native": read_json(OUT / "native-right-all.json"),
            "learner": read_json(OUT / "learner-structure.json"),
            "evidence": read_json(OUT / "independent-evidence.json"),
            "pairs": read_json(OUT / "class-pair-summary.json"),
        }
        self.assertEqual(digest(source), summary["summary_digest"])
        self.assertEqual(digest(copy.deepcopy(source)), summary["summary_digest"])
        for r in read_json(OUT / "weight-bins-complete.json"):
            if r["n"]:
                self.assertEqual(r["flip_rate"], r["flips"] / r["n"])
                self.assertEqual(r["base_accuracy"], 1 - r["base_wrong"] / r["n"])

    def test_frozen_manifest_heads_and_selection(self):
        before = read_json(OUT / "freeze-before.json")["files"]
        for p in (PRIOR / "representation-manifest.json", PRIOR / "predictions.json"):
            self.assertEqual(file_hash(p), before[str(p.relative_to(ROOT))])
        from perceptual_tone.pooling_blocker_audit import LOCK

        for model in read_json(LOCK)["model_method"]["models"].values():
            self.assertEqual(file_hash(model["path"]), model["sha256"])
        self.assertEqual(
            file_hash(OUT / "selection.json"),
            read_json(OUT / "audit-preregistration.json")["selection_sha256"],
        )


if __name__ == "__main__":
    unittest.main()

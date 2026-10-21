"""Lightweight validation of the actual completed review and failure guards.

Mutated test answers exist only in memory, never in the human export or packet.
No audio rendering, model deserialization, inference or training is invoked.
"""

import ast
import copy
import unittest
from pathlib import Path

from perceptual_tone import blind_analysis as b
from perceptual_tone.blind_analysis_report import render
from perceptual_tone.blind_packet import LEARNER, OUTPUT
from perceptual_tone.common import PACKAGE, digest, file_hash, read_json, read_rows
from perceptual_tone.manifest import verify_baseline

RUN = OUTPUT.parent / "realized-tone-analysis-v1-20261019"


class BlindAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = read_json(OUTPUT / "private/packet-manifest.json")
        cls.review = read_json(RUN / "human-export.original.json")
        cls.key = read_json(OUTPUT / "private/answer-key.json")
        cls.joined = b.join_key(cls.review, cls.key)
        cls.stage = read_json(RUN / "02-controls-and-repeats.json")
        cls.gate = read_json(RUN / "03-reliability-gate.json")
        cls.release = read_rows(LEARNER / "primary.jsonl")
        cls.analysis = b.learner_analysis(cls.joined, cls.release, cls.stage, cls.gate)

    def test_export_schema_identity_and_original_bytes(self):
        self.assertEqual(b.validate_export(self.manifest, self.review)["presentations"], 52)
        original = Path("/home/jacob/Downloads/benma-realized-tone-blind-review.json")
        self.assertEqual(original.read_bytes(), (RUN / "human-export.original.json").read_bytes())
        self.assertEqual(
            file_hash(original), read_json(RUN / "01-export-validation.json")["export_sha256"]
        )
        for field, value in [
            ("schema", "wrong"),
            ("packet_version", "wrong"),
            ("packet_sha256", "wrong"),
            ("reviewer", "Someone else"),
        ]:
            r = copy.deepcopy(self.review)
            r[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                b.validate_export(self.manifest, r)
        for operation in ("missing", "duplicate", "reordered"):
            r = copy.deepcopy(self.review)
            if operation == "missing":
                r["reviews"].pop()
            if operation == "duplicate":
                r["reviews"][0] = r["reviews"][1]
            if operation == "reordered":
                r["reviews"].reverse()
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                b.validate_export(self.manifest, r)

    def test_export_choice_confidence_telemetry_and_timestamp(self):
        for field, value in [
            ("perceived_tone", "T5"),
            ("confidence", True),
            ("confidence", 6),
            ("tone_bearing_heard", False),
            ("whole_target_heard", 1),
            ("timestamp", "2026-10-19T00:00:00"),
            ("usability", "GOOD"),
        ]:
            r = copy.deepcopy(self.review)
            r["reviews"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                b.validate_export(self.manifest, r)
        r = copy.deepcopy(self.review)
        r["reviews"][0]["unexpected"] = 1
        with self.assertRaises(ValueError):
            b.validate_export(self.manifest, r)

    def test_packet_audio_tamper_rejected(self):
        m = copy.deepcopy(self.manifest)
        m["items"][0]["audio"]["tone"] = "changed"
        with self.assertRaisesRegex(ValueError, "packet_hash"):
            b.validate_export(m, self.review)

    def test_join_rejects_wrong_key_and_repeat_identity(self):
        for mutation in ("hash", "id", "repeat"):
            k = copy.deepcopy(self.key)
            if mutation == "hash":
                k["packet_sha256"] = "wrong"
            if mutation == "id":
                k["items"][0]["annotation_id"] = "wrong"
            if mutation == "repeat":
                next(x for x in k["items"] if x["duplicate_of"])["unit_id"] = "wrong"
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                b.join_key(self.review, k)

    def test_control_only_first_stage_reproduces_saved_artifact(self):
        self.assertEqual(b.first_stage(self.joined), self.stage)
        poisoned = copy.deepcopy(self.joined)
        for r in poisoned:
            for key in (
                "expanded_model_result",
                "pilot_model_result",
                "expected_surface_tone",
                "deterministic_result",
            ):
                r[key] = "POISONED"
            if (
                r["base_role"] == "learner"
                and not r["duplicate_of"]
                and not any(x["duplicate_of"] == r["annotation_id"] for x in poisoned)
            ):
                r["human"]["perceived_tone"] = "NEUTRAL"
        self.assertEqual(b.first_stage(poisoned), self.stage)
        self.assertNotIn("expanded_model_result", str(self.stage))

    def test_control_matrix_and_denominators(self):
        c = self.stage["controls"]
        self.assertEqual(
            [c["matrix"][t][p] for t in b.TONES[:-1] for p in b.TONES],
            [
                1,
                0,
                2,
                1,
                0,
                2,
                2,
                1,
                2,
                0,
                1,
                0,
                1,
                0,
                4,
                1,
                0,
                0,
                0,
                1,
                0,
                3,
                0,
                2,
                0,
                0,
                2,
                0,
                1,
                1,
            ],
        )
        self.assertEqual(c["full_exact"], b.fraction(10, 28))
        self.assertEqual(c["numbered_reference_coverage"], b.fraction(19, 24))
        self.assertEqual(c["numbered_reference_conditional"], b.fraction(9, 19))
        self.assertEqual(c["numbered_judgment_conditional_all_controls"], b.fraction(9, 21))

    def test_abstention_and_neutral_are_distinct(self):
        synthetic = [
            {"native_control_gold_tone": t, "human": {"perceived_tone": p}}
            for t, p in [("T1", "T1"), ("T1", "UNCLEAR"), ("NEUTRAL", "NEUTRAL"), ("NEUTRAL", "T2")]
        ]
        c = b.control_metrics(synthetic)
        self.assertEqual(c["full_exact"], b.fraction(2, 4))
        self.assertEqual(c["numbered_reference_conditional"], b.fraction(1, 1))
        self.assertEqual(c["numbered_reference_coverage"], b.fraction(1, 2))
        self.assertEqual(c["numbered_judgment_conditional_all_controls"], b.fraction(1, 2))
        self.assertEqual(c["recall"]["NEUTRAL"], b.fraction(1, 2))

    def test_all_eight_repeats_and_unclear_success(self):
        self.assertEqual(len(self.stage["pairs"]), 8)
        self.assertEqual(self.stage["repeat_exact"], b.fraction(3, 8))
        self.assertEqual(self.stage["repeat_informative_exact"], b.fraction(2, 8))
        self.assertEqual(self.stage["repeat_numbered"], b.fraction(2, 4))
        self.assertEqual(self.stage["unclear_transitions"], 3)
        unclear = [
            p
            for p in self.stage["pairs"]
            if p["exact"] and p["first"]["perceived_tone"] == "UNCLEAR"
        ]
        self.assertEqual(len(unclear), 1)
        self.assertFalse(unclear[0]["informative_exact"])
        self.assertEqual(self.stage["mean_absolute_confidence_delta"], 1)

    def test_registered_checks_exactly_preserved(self):
        checks = b.registered_checks(self.stage, self.review)
        self.assertEqual(checks, read_json(RUN / "03-registered-checks.json"))
        self.assertFalse(any(checks["criteria"].values()))
        self.assertEqual(len(checks["criteria"]), 7)

    def test_preregistered_boundaries_and_unusable_not_success(self):
        s = copy.deepcopy(self.stage)
        s["controls"]["full_exact"] = b.fraction(23, 28)
        s["controls"]["numbered_reference_full"] = b.fraction(20, 24)
        s["controls"]["recall"] = {t: b.fraction(5, 6) for t in b.NUMBERED}
        s["controls"]["recall"]["NEUTRAL"] = b.fraction(3, 4)
        s["repeat_informative_exact"] = b.fraction(7, 8)
        r = copy.deepcopy(self.review)
        for row in r["reviews"]:
            row.update(confidence=3, perceived_tone="T1")
        self.assertTrue(b.registered_checks(s, r)["passed"])
        s["controls"]["full_exact"] = b.fraction(22, 28)
        self.assertFalse(b.registered_checks(s, r)["passed"])
        s["controls"]["full_exact"] = b.fraction(23, 28)
        s["control_rows"][0]["human"].update(
            usability="UNUSABLE", perceived_tone=s["control_rows"][0]["native_control_gold_tone"]
        )
        self.assertFalse(b.registered_checks(s, r)["criteria"]["full_control_23_of_28"])

    def test_frozen_gate_and_exploratory_only_guards(self):
        self.assertEqual(digest(self.gate), b.FROZEN_GATE_SHA)
        self.assertEqual(self.gate["classification"], "INSUFFICIENT")
        self.assertFalse(self.gate["confirmatory_model_evaluation_permitted"])
        self.assertEqual(self.analysis["status"], "EXPLORATORY_ONLY_NOT_TRANSFER_VALIDATION")
        for field, value in [
            ("classification", "STRONG"),
            ("rationale", "changed"),
            ("basis", "learner_model_agreement"),
        ]:
            g = copy.deepcopy(self.gate)
            g[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                b.learner_analysis(self.joined, self.release, self.stage, g)
        s = copy.deepcopy(self.stage)
        s["controls"]["full_exact"]["n"] = 28
        with self.assertRaises(ValueError):
            b.learner_analysis(self.joined, self.release, s, self.gate)

    def test_exact_learner_population_and_metadata(self):
        rows = self.analysis["rows"]
        self.assertEqual(len(rows), 16)
        self.assertEqual({r["unit_id"] for r in rows}, {r["example_id"] for r in self.release})
        self.assertEqual(len({r["qa_id"] for r in rows}), 16)
        self.assertEqual(
            self.analysis["tone_distribution"],
            {"T1": 3, "T2": 0, "T3": 6, "T4": 3, "NEUTRAL": 0, "UNCLEAR": 4},
        )
        with self.assertRaises(ValueError):
            b.learner_analysis(self.joined, self.release[:-1], self.stage, self.gate)

    def test_expected_numbered_and_neutral_denominators(self):
        a = self.analysis
        self.assertEqual(len(a["expected_numbered_rows"]), 10)
        self.assertEqual(len(a["expected_neutral_rows"]), 1)
        self.assertEqual(a["expected_human_numbered_full"], b.fraction(6, 10))
        self.assertEqual(a["expected_human_numbered_conditional"], b.fraction(6, 8))
        self.assertEqual(a["expected_human_numbered_coverage"], b.fraction(8, 10))
        self.assertEqual(a["expected_human_full"], b.fraction(6, 11))
        self.assertEqual(a["models_vs_expected_same_human_subset"]["expanded"], b.fraction(4, 8))
        self.assertEqual(a["models_vs_human_same_expected_subset"]["expanded"], b.fraction(5, 8))

    def test_neutral_human_not_coerced_or_four_tone_scored(self):
        j = copy.deepcopy(self.joined)
        target = next(
            r for r in j if r["role"] == "learner" and r["human"]["perceived_tone"] == "T1"
        )
        target["human"]["perceived_tone"] = "NEUTRAL"
        a = b.learner_analysis(j, self.release, self.stage, self.gate)
        self.assertEqual(a["tone_distribution"]["NEUTRAL"], 1)
        self.assertEqual(a["strata"]["1"]["expanded"]["d"], 11)
        self.assertEqual(a["non_unclear_comparison"]["expanded"]["d"], 12)
        self.assertEqual(len(a["excluded_numbered_scoring"]["neutral"]), 1)
        self.assertIn(a["excluded_numbered_scoring"]["neutral"][0]["expanded"], b.NUMBERED)

    def test_confidence_strata_and_missing_usability(self):
        expected = [(6, 8, 12), (5, 7, 11), (1, 3, 4), (1, 2, 2)]
        for t, (e, p, n) in zip(("1", "2", "3", "4"), expected, strict=True):
            self.assertEqual(self.analysis["strata"][t]["expanded"], b.fraction(e, n))
            self.assertEqual(self.analysis["strata"][t]["pilot"], b.fraction(p, n))
        self.assertEqual(self.analysis["high_confidence_clear"]["expanded"], b.fraction(1, 1))
        self.assertEqual(self.analysis["excluded_numbered_scoring"]["usability_unspecified"], 11)
        self.assertEqual(self.analysis["whole_target_usage"], b.fraction(11, 16))
        self.assertEqual(len(self.analysis["confidence_at_least_3_rows"]), 6)

    def test_seven_t2_cases_retained_without_confidence_filter(self):
        cases = self.analysis["t2_disagreement_rows"]
        self.assertEqual(len(cases), 7)
        self.assertTrue(all(r["expanded"] == "T2" and r["pilot"] != "T2" for r in cases))
        self.assertEqual(
            self.analysis["t2_human_distribution"],
            {"T1": 1, "T2": 0, "T3": 3, "T4": 0, "NEUTRAL": 0, "UNCLEAR": 3},
        )
        self.assertEqual(sum(r["human"]["perceived_tone"] == "UNCLEAR" for r in cases), 3)

    def test_repeat_ids_map_to_correct_learner_cases(self):
        rows = {r["annotation_id"]: r for r in self.analysis["rows"]}
        cases = [
            (rows[p["original_id"]]["take"], rows[p["original_id"]]["hanzi"])
            for p in self.stage["pairs"]
            if p["base_role"] == "learner"
        ]
        self.assertEqual(cases, [("S01", "走"), ("S03", "水"), ("S02", "晚")])

    def test_report_generation_and_all_required_cases(self):
        checks = read_json(RUN / "03-registered-checks.json")
        freeze = read_json(RUN / "06-freeze-verification.json")
        report = render(self.review, self.stage, self.gate, checks, self.analysis, freeze)
        self.assertEqual(
            report, (PACKAGE / "realized-tone-reliability-first-report.md").read_text()
        )
        self.assertEqual(self.analysis, read_json(RUN / "05-final-exploratory-analysis.json"))
        for r in self.analysis["rows"]:
            self.assertIn(r["unit_id"], report)
        for p in self.stage["pairs"]:
            self.assertIn(p["original_id"], report)
            self.assertIn(p["repeat_id"], report)
        for phrase in (
            "EXPLORATORY SOLO PERCEPTUAL ANNOTATION",
            "C — SOLO LABELS INSUFFICIENT",
            "28 presentations",
            "MIXED / unresolved",
            "NO GENERAL IMPROVEMENT DEMONSTRATED",
            "F0",
            "competent Mandarin listener",
        ):
            self.assertIn(phrase, report)
        self.assertNotIn("S02 天 changes", report)

    def test_no_training_model_loading_or_adaptation_entry_points(self):
        for filename in (
            PACKAGE / "perceptual_tone/blind_analysis.py",
            PACKAGE / "perceptual_tone/blind_analysis_report.py",
            PACKAGE / "scripts/blind_analysis.py",
        ):
            tree = ast.parse(filename.read_text())
            forbidden = {"torch", "transformers", "sklearn", "joblib", "learner_transfer"}
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertFalse({a.name.split(".")[0] for a in node.names} & forbidden)
                if isinstance(node, ast.ImportFrom):
                    self.assertFalse(set((node.module or "").split(".")) & forbidden)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    self.assertNotIn(
                        node.func.attr,
                        {
                            "fit",
                            "fit_transform",
                            "partial_fit",
                            "from_pretrained",
                            "predict",
                            "predict_proba",
                        },
                    )
        self.assertTrue(self.analysis["no_training_adaptation_or_inference"])

    def test_413_baseline_and_production_freeze_record(self):
        self.assertEqual(verify_baseline()["verified_files"], 413)
        freeze = read_json(RUN / "06-freeze-verification.json")
        self.assertEqual(freeze["baseline_hashes_unchanged"], 413)
        self.assertTrue(freeze["production_inference_grading_ui_apis_deployment_unchanged"])
        self.assertEqual(freeze["status"], "PASS")


if __name__ == "__main__":
    unittest.main()

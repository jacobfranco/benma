"""Continuation contracts. Uses saved manifests only; no discovery, aligner or model runs."""

import ast
import copy
import unittest
from pathlib import Path

from perceptual_tone import learner_finalization as f
from perceptual_tone.common import digest, file_hash, read_json, read_rows


class FinalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.master = read_rows(f.DEFAULT / "master-inventory.jsonl")
        cls.units = read_rows(f.DEFAULT / "candidate-manifest.jsonl")
        cls.packet = read_json(f.DEFAULT / "qa/packet.json")
        cls.old = read_rows(f.CONSTRUCTION / "candidate-manifest.jsonl")

    def test_categories_natural_only_and_diagnostic_preserved(self):
        primary = [u for u in self.units if u["primary_natural_candidate"]]
        self.assertEqual(len(primary), 32)
        self.assertEqual(len({u["source_id"] for u in primary}), 3)
        diag = [u for u in self.units if u["provenance_category"] == f.DIAGNOSTIC]
        self.assertEqual(len(diag), 12)
        self.assertTrue(
            all(not u["primary_natural_candidate"] and u["historical_role"] for u in diag)
        )
        self.assertEqual(sum(u["provenance_hold"] for u in self.units), 79)
        short = [r for r in self.master if r["alignment_transcript"] == "我想买"]
        self.assertEqual(len(short), 6)
        self.assertTrue(
            all(
                r["provenance_category"] == f.UNKNOWN and r["capture_intent"] is None for r in short
            )
        )

    def test_controls_and_unknown_identity_are_not_inferred(self):
        self.assertEqual(sum(r["provenance_category"] == f.CONTROL for r in self.master), 7)
        self.assertEqual(sum(r["human_control_status"] == "human" for r in self.master), 8)
        self.assertEqual(sum(r["material_category"] == f.UNUSABLE for r in self.master), 113)
        self.assertTrue(
            all(
                not r["primary_benchmark_candidate"]
                for r in self.master
                if r["provenance_category"] != f.NATURAL
            )
        )
        special = [r for r in self.master if r["alignment_transcript"] == "我想买这个"]
        self.assertEqual(len(special), 7)
        self.assertEqual(sum(r["provenance_category"] == f.CONTROL for r in special), 2)

    def test_review_flags_are_not_structural_failures(self):
        self.assertEqual(sum(bool(u["alignment_flags"]) for u in self.units), 37)
        self.assertTrue(
            all(
                not u["structural_violations"]
                and not u["alignment_quarantined"]
                and not u["exclusion_reasons"]
                and u["reconstruction_status"] == "structurally_valid_qa_pending"
                for u in self.units
            )
        )
        row = copy.deepcopy(self.old[0])
        row["flags"] = list(f.REVIEW_FLAGS)
        self.assertEqual(f.structural_issues(row), [])
        row["spans"]["tone_bearing_pooling_span"]["end_sample"] += 1
        self.assertIn("invalid_nested_sample_ownership", f.structural_issues(row))

    def test_candidate_reproduction_and_distinct_label_fields(self):
        self.assertEqual(self.units, f.compile_candidates(list(reversed(self.old)), self.master))
        self.assertTrue(
            all(
                u["model_prediction"] is None
                and u["realized_tone_ground_truth"] is None
                and u["qa_status"] == "PENDING"
                and not u["eligible_for_evaluation"]
                for u in self.units
            )
        )
        substituted = [
            u
            for u in self.units
            if u["intended_pinyin"] == "guang3" and u["alignment_pinyin"] == "gui4"
        ]
        self.assertEqual(len(substituted), 1)
        self.assertEqual(substituted[0]["expected_surface_tone"], 3)
        self.assertEqual(substituted[0]["alignment_lexical_tone"], 4)

    def test_order_randomization_and_packet_reproducibility(self):
        old_packet = read_json(f.CONSTRUCTION / "qa/packet.json")
        actual = f.make_packet(
            list(reversed(self.units)),
            old_packet,
            file_hash(f.DEFAULT / "candidate-manifest.jsonl"),
        )
        self.assertEqual(actual, self.packet)
        self.assertNotEqual(
            [i["unit_id"] for i in actual["items"]], [i["example_id"] for i in old_packet["items"]]
        )
        for item in actual["items"]:
            self.assertEqual(
                item["item_sha256"], digest({k: v for k, v in item.items() if k != "item_sha256"})
            )

    def test_lineage_preserves_copies_of_clips_and_is_deterministic(self):
        artifacts = read_rows(f.CONSTRUCTION / "audio-artifacts.jsonl")
        graph = f.lineage(list(reversed(self.master)), list(reversed(artifacts)))
        self.assertEqual(graph, read_json(f.DEFAULT / "source-lineage.json"))
        self.assertEqual(graph["counts"]["exact_duplicate_copies_beyond_first"], 247)
        self.assertEqual(graph["counts"]["clip_or_clip_copy_artifacts"], 223)
        self.assertEqual(
            graph["counts"]["whole_source_byte_different_representations_beyond_first"], 168
        )
        self.assertEqual(len({n["id"] for n in graph["nodes"]}), len(graph["nodes"]))

    def test_export_identity_heard_flags_and_tamper_gate(self):
        packet = copy.deepcopy(self.packet)
        packet["items"] = packet["items"][:1]
        item = packet["items"][0]
        row = {
            k: item[k]
            for k in ["item_id", "unit_id", "source_id", "item_sha256", "alignment_flags"]
        }
        row.update(
            whole="PASS",
            tone="PASS",
            notes="",
            heard_all=True,
            heard={"context": True, "whole": True, "tone": True},
            reviewer="SYNTHETIC TEST",
            reviewed_at="2026-10-19T00:00:00Z",
        )
        answers = {
            "schema": packet["schema"],
            "packet_sha256": packet["packet_sha256"],
            "reviewer": "SYNTHETIC TEST",
            "reviews": [row],
        }
        self.assertEqual(f.validate_reviews(packet, answers)["reviews"], 1)
        for field, value in [
            ("unit_id", "wrong"),
            ("source_id", "wrong"),
            ("item_sha256", "wrong"),
            ("alignment_flags", ["invented"]),
            ("heard", {"context": True, "whole": True, "tone": "false"}),
            ("reviewed_at", "not a date"),
            ("tone", "CLIPPED"),
        ]:
            bad = copy.deepcopy(answers)
            bad["reviews"][0][field] = value
            with self.assertRaises(ValueError):
                f.validate_reviews(packet, bad)
        duplicate = copy.deepcopy(answers)
        duplicate["reviews"].append(row)
        with self.assertRaises(ValueError):
            f.validate_reviews(packet, duplicate)

    def test_no_discovery_scoring_training_or_alignment_invocation(self):
        tree = ast.parse(Path(f.__file__).read_text())
        imports = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        self.assertFalse(
            any(
                any(
                    word in name
                    for word in ["torch", "transformers", "joblib", "embeddings", "learning"]
                )
                for name in imports
            )
        )
        calls = {
            n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id
            for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, (ast.Attribute, ast.Name))
        }
        self.assertFalse(
            {"discover", "fit", "predict", "predict_proba", "align", "extract"} & calls
        )

    def test_master_reproducible_from_existing_metadata_only(self):
        rebuilt = f.master_inventory(
            read_rows(f.CONSTRUCTION / "inventory.jsonl"), self.old, read_json(f.CONFIG)
        )
        self.assertEqual(rebuilt, self.master)
        self.assertEqual(sum(r["capture_date"] is not None for r in rebuilt), 57)
        self.assertTrue(
            all(
                r["capture_date"]["event"] == "audio_asset_created_at"
                for r in rebuilt
                if r["capture_date"]
            )
        )


if __name__ == "__main__":
    unittest.main()

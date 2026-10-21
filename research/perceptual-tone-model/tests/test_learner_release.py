"""Substantive human QA contracts, quarantine policy, and immutable release gates."""

import ast
import copy
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from perceptual_tone import learner_release as release
from perceptual_tone.common import file_hash, read_json, read_rows, write_json
from perceptual_tone.learner_finalization import DEFAULT, validate_reviews


class LearnerReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = read_json(DEFAULT / "qa/packet.json")
        cls.answers = read_json(release.DRAFT)
        cls.units = read_rows(DEFAULT / "candidate-manifest.jsonl")

    def test_real_draft_completeness_and_exact_telemetry(self):
        before = copy.deepcopy(self.answers)
        result = validate_reviews(self.packet, self.answers)
        self.assertEqual(result["reviews"], 123)
        self.assertEqual((result["whole_nonpass"], result["tone_nonpass"]), (21, 21))
        self.assertEqual(self.answers, before)
        self.assertEqual(
            [
                sum(not r["heard"][k] for r in self.answers["reviews"])
                for k in ("context", "whole", "tone")
            ],
            [86, 16, 3],
        )
        self.assertEqual(sum(not r["heard_all"] for r in self.answers["reviews"]), 86)

    def test_playback_is_optional_and_never_decides_completion(self):
        for absent in (False, True):
            answers = copy.deepcopy(self.answers)
            for row in answers["reviews"]:
                row["heard"] = dict.fromkeys(("context", "whole", "tone"), False)
                row["heard_all"] = False
                if absent:
                    del row["heard"], row["heard_all"]
            self.assertEqual(validate_reviews(self.packet, answers)["reviews"], 123)
        answers = copy.deepcopy(self.answers)
        for row in answers["reviews"]:
            if row["whole"] == row["tone"] == "PASS":
                del row["notes"]
        self.assertEqual(validate_reviews(self.packet, answers)["reviews"], 123)

    def test_exact_missing_fields_schema_ids_hashes_and_note_requirements(self):
        for field in ("whole", "tone", "notes"):
            bad = copy.deepcopy(self.answers)
            row = next(r for r in bad["reviews"] if r["tone"] != "PASS")
            row[field] = ""
            with self.assertRaisesRegex(ValueError, field):
                validate_reviews(self.packet, bad)
        for field in ("schema", "packet_sha256", "reviewer"):
            bad = copy.deepcopy(self.answers)
            bad[field] = ""
            with self.assertRaises(ValueError):
                validate_reviews(self.packet, bad)
        for field in ("unit_id", "source_id", "item_sha256", "item_id"):
            bad = copy.deepcopy(self.answers)
            bad["reviews"][0][field] = "wrong"
            with self.assertRaises(ValueError):
                validate_reviews(self.packet, bad)
        bad = copy.deepcopy(self.answers)
        bad["reviews"][-1] = bad["reviews"][0]
        with self.assertRaises(ValueError):
            validate_reviews(self.packet, bad)

    def test_adjudication_inventory_and_primary_separation(self):
        answers = {r["unit_id"]: r for r in self.answers["reviews"]}
        items = {r["unit_id"]: r for r in self.packet["items"]}
        rows = [
            release.adjudicate(u, answers[u["example_id"]], items[u["example_id"]])
            for u in self.units
        ]
        self.assertEqual(sum(r["adjudication_required"] for r in rows), 22)
        self.assertEqual(sum(r["quarantined"] for r in rows), 21)
        self.assertEqual(
            Counter((r["provenance_category"], r["quarantined"]) for r in rows),
            {
                (release.NATURAL, False): 16,
                (release.NATURAL, True): 16,
                (release.DIAGNOSTIC, False): 11,
                (release.DIAGNOSTIC, True): 1,
                (release.UNKNOWN, False): 75,
                (release.UNKNOWN, True): 4,
            },
        )
        bu = next(r for r in rows if r["qa_item_id"] == "Q037")
        self.assertEqual(bu["adjudication"], "PASS_AS_IS")
        self.assertTrue(all(r["qa"] == answers[r["example_id"]] for r in rows))
        self.assertTrue(all(not r["eligible_for_training"] for r in rows))
        self.assertTrue(all(r["eligible_for_evaluation"] != r["quarantined"] for r in rows))

    def test_saved_reconstruction_has_no_general_projection_defect(self):
        audit = release.alignment_audit(self.units)
        self.assertEqual(audit["reconstructed_units"], 123)
        self.assertEqual(audit["mismatches"], [])
        self.assertFalse(audit["systematic_bug_found"])

    def test_existing_release_cannot_be_rewritten_and_tamper_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            with self.assertRaisesRegex(ValueError, "release_exists_immutable"):
                release.freeze(destination=path)
            write_json(path / "payload.json", {"data": "original"})
            write_json(
                path / "release-manifest.json",
                {"files": {"payload.json": file_hash(path / "payload.json")}},
            )
            write_json(
                path / "release-seal.json",
                {"manifest_sha256": file_hash(path / "release-manifest.json")},
            )
            (path / "payload.json").write_text("tampered")
            with self.assertRaisesRegex(ValueError, "immutable_release_file_changed"):
                release.verify_release(path)

    def test_release_module_cannot_train_or_predict(self):
        tree = ast.parse(Path(release.__file__).read_text())
        calls = {
            n.func.attr
            for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        }
        self.assertFalse({"fit", "partial_fit", "predict", "predict_proba", "backward"} & calls)


if __name__ == "__main__":
    unittest.main()

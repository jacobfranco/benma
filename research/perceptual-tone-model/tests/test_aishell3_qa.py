"""Gate failures must remain failures; synthetic tests are never playback evidence."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from perceptual_tone.aishell3 import size_balanced_speaker_split
from perceptual_tone.aishell3_qa import DECISIONS, dataset_gate, validate_reviews
from perceptual_tone.common import PACKAGE, digest, file_hash, write_json, write_rows

sys.path.insert(0, str(PACKAGE / "scripts"))
from aishell3_continue import ingest, release, verified_packet


class PlaybackGateTests(unittest.TestCase):
    def setUp(self):
        self.items = [
            {"row": {"example_id": f"test:{i}", "label": f"T{i + 1}", "start": 0.1, "end": 0.3}}
            for i in range(4)
        ]
        self.reviews = [
            {
                "example_id": item["row"]["example_id"],
                "item_sha256": digest(item["row"]),
                "reviewer": "SYNTHETIC TEST ONLY",
                "reviewed_at": "2026-10-16T15:00:00Z",
                "decision": "PASS",
                "heard_context_and_target": True,
                "notes": "",
            }
            for item in self.items
        ]

    def test_empty_or_incomplete_is_pending_never_inferred(self):
        with self.assertRaisesRegex(ValueError, "empty_review_packet"):
            validate_reviews([], [], complete=True)
        self.assertEqual(validate_reviews(self.items, [])[1]["status"], "pending")
        self.assertEqual(validate_reviews(self.items, self.reviews[:1])[1]["status"], "pending")
        with self.assertRaisesRegex(ValueError, "incomplete_packet_review"):
            validate_reviews(self.items, self.reviews[:1], complete=True)

    def test_all_explicit_decisions_and_playback_confirmation_required(self):
        self.assertEqual(
            validate_reviews(self.items, self.reviews, complete=True)[1]["status"], "passed"
        )
        for field, value in [
            ("heard_context_and_target", False),
            ("heard_context_and_target", 1),
            ("decision", ""),
            ("decision", "tone sounds good"),
            ("reviewer", " "),
            ("reviewed_at", "2026-10-16T15:00:00"),
            ("reviewed_at", None),
        ]:
            with self.subTest(field=field, value=value):
                reviews = copy.deepcopy(self.reviews)
                reviews[0][field] = value
                with self.assertRaises(ValueError):
                    validate_reviews(self.items, reviews, complete=True)

    def test_every_nonpass_blocks_without_relabeling(self):
        originals = copy.deepcopy(self.items)
        for decision in DECISIONS[1:]:
            reviews = copy.deepcopy(self.reviews)
            reviews[0].update(decision=decision, notes="SYNTHETIC issue")
            self.assertEqual(
                validate_reviews(self.items, reviews, complete=True)[1]["status"], "failed"
            )
            reviews[0]["notes"] = ""
            with self.assertRaisesRegex(ValueError, "nonpass_requires_notes"):
                validate_reviews(self.items, reviews)
        self.assertEqual(self.items, originals)

    def test_stale_boundary_hash_duplicate_and_unknown_ids_rejected(self):
        items = copy.deepcopy(self.items)
        items[0]["row"]["end"] = 0.31
        with self.assertRaisesRegex(ValueError, "review_not_bound"):
            validate_reviews(items, self.reviews)
        with self.assertRaisesRegex(ValueError, "unknown_or_duplicate"):
            validate_reviews(self.items, self.reviews + self.reviews[:1])
        reviews = copy.deepcopy(self.reviews)
        reviews[0]["example_id"] = "unknown"
        with self.assertRaisesRegex(ValueError, "unknown_or_duplicate"):
            validate_reviews(self.items, reviews)

    def make_packet(self, root):
        folder = root / "pilot/audit/review"
        folder.mkdir(parents=True)
        (folder / "audio.wav").write_bytes(b"synthetic media hash fixture")
        media = {"reference": "audio.wav", "sha256": file_hash(folder / "audio.wav")}
        items = [
            {
                **item,
                "item": f"item-{index}",
                "item_sha256": digest(item["row"]),
                "playback": {"target": media},
                "plot": media,
            }
            for index, item in enumerate(self.items)
        ]
        payload = {
            "schema": "aishell3-playback-integrity-v1",
            "decisions": list(DECISIONS),
            "items": items,
        }
        packet = {**payload, "packet_sha256": digest(payload)}
        write_json(folder / "packet.json", packet)
        write_rows(
            folder / "items.jsonl",
            [{k: item[k] for k in ("item", "row", "playback")} for item in items],
        )
        write_rows(root / "pilot/audit/candidates.jsonl", [i["row"] for i in items])
        return packet

    def test_browser_export_ingestion_binds_packet_and_preserves_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = self.make_packet(root)
            reviews = copy.deepcopy(self.reviews)
            reviews[1].update(decision="BOUNDARY EARLY", notes="SYNTHETIC issue")
            write_json(
                root / "export.json",
                {
                    "schema": packet["schema"],
                    "packet_sha256": packet["packet_sha256"],
                    "reviews": reviews,
                },
            )
            status = ingest(root, root / "export.json", root / "decisions.jsonl")
            self.assertEqual(status["status"], "failed")
            rows = [
                json.loads(line) for line in (root / "decisions.jsonl").read_text().splitlines()
            ]
            self.assertTrue(all(r["packet_sha256"] == packet["packet_sha256"] for r in rows))
            self.assertEqual(rows[1]["decision"], "BOUNDARY EARLY")

    def test_packet_media_and_candidate_tampering_rejected(self):
        for corruption in ("packet", "media", "candidate"):
            with self.subTest(corruption=corruption), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                packet = self.make_packet(root)
                if corruption == "packet":
                    packet["items"][0]["row"]["end"] = 9
                    (root / "pilot/audit/review/packet.json").write_text(json.dumps(packet))
                elif corruption == "media":
                    (root / "pilot/audit/review/audio.wav").write_bytes(b"changed")
                else:
                    (root / "pilot/audit/candidates.jsonl").write_text("{}\n")
                with self.assertRaises((ValueError, KeyError)):
                    verified_packet(root)

    def test_wrong_packet_or_incomplete_export_does_not_write_decisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = self.make_packet(root)
            for suffix, raw in (
                (
                    "wrong",
                    {"schema": packet["schema"], "packet_sha256": "wrong", "reviews": self.reviews},
                ),
                (
                    "empty",
                    {
                        "schema": packet["schema"],
                        "packet_sha256": packet["packet_sha256"],
                        "reviews": [],
                    },
                ),
            ):
                write_json(root / (suffix + ".json"), raw)
                with self.assertRaises(ValueError):
                    ingest(root, root / (suffix + ".json"), root / "decisions.jsonl")
                self.assertFalse((root / "decisions.jsonl").exists())

    def test_release_remains_closed_without_real_complete_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = self.make_packet(root)
            automatic = {"automatic_qa": "passed", "core_coverage_gate": {"passed": True}}
            for index, reviews in enumerate(([], self.reviews)):
                decisions = copy.deepcopy(reviews)
                for review in decisions:
                    review.update(packet_sha256=packet["packet_sha256"])
                if decisions:
                    decisions[0].update(decision="OTHER", notes="SYNTHETIC uncertain ownership")
                path = root / f"decisions-{index}.jsonl"
                write_rows(path, decisions)
                with (
                    patch("aishell3_continue.audit", return_value=automatic),
                    self.assertRaises(ValueError),
                ):
                    release(root, path, root / "released")
                self.assertFalse((root / "released").exists())


class DatasetGateTests(unittest.TestCase):
    def test_size_split_uses_only_counts_is_order_invariant_and_disjoint(self):
        counts = {f"SSB{i:04d}": i * 7 + 1 for i in range(16)}
        split = size_balanced_speaker_split(counts)
        self.assertEqual(split, size_balanced_speaker_split(dict(reversed(list(counts.items())))))
        self.assertEqual(sorted(split.values()).count("test"), 3)
        self.assertEqual(sorted(split.values()).count("validation"), 3)
        self.assertEqual(sorted(split.values()).count("train"), 10)
        with self.assertRaises(ValueError):
            size_balanced_speaker_split({"one": 2})

    def test_four_core_classes_can_pass_without_neutral(self):
        rows = [
            {
                "example_id": str(i),
                "speaker_id": f"s{i % 12}",
                "utterance_id": str(i),
                "pcm_sha256": str(i),
                "partition": ("train", "validation", "test")[i % 3],
                "label": f"T{(i // 12) % 4 + 1}",
            }
            for i in range(600)
        ]
        self.assertTrue(dataset_gate(rows)["passed"])
        poor = [r for r in rows if not (r["partition"] == "test" and r["label"] == "T3")]
        self.assertIn("core_class_coverage_test", dataset_gate(poor)["blockers"])
        leaked = copy.deepcopy(rows)
        leaked[1]["pcm_sha256"] = leaked[0]["pcm_sha256"]
        with self.assertRaisesRegex(ValueError, "split_leakage_pcm"):
            dataset_gate(leaked)


if __name__ == "__main__":
    unittest.main()

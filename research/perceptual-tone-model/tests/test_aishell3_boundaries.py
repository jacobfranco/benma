import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from perceptual_tone.aishell3_boundaries import derive, sample_index, span
from perceptual_tone.aishell3_qa import decode
from perceptual_tone.common import PACKAGE, digest, write_json

sys.path.insert(0, str(PACKAGE / "scripts"))
from aishell3_round2 import (
    FINAL_DECISIONS,
    SCHEMA,
    WHOLE_DECISIONS,
    export_clip,
    ingest_round2,
    render,
)


def row_for(phones):
    intervals = [
        {"start": round(0.2 + i * 0.1, 2), "end": round(0.3 + i * 0.1, 2), "phone": phone}
        for i, phone in enumerate(phones)
    ]
    return {
        "example_id": "synthetic:unit",
        "start": intervals[0]["start"],
        "end": intervals[-1]["end"],
        "aligned_phones": intervals,
        "label": "T3",
        "corpus_pinyin": "synthetic3",
        "hanzi": "测试",
        "speaker_id": "synthetic",
        "utterance_id": "test",
        "transcript": "synthetic only",
        "preceding": None,
        "following": None,
    }


class SampleOwnershipTests(unittest.TestCase):
    def test_float_floor_ceil_defect_has_shared_boundary_without_gap_or_duplication(self):
        rate = 44100
        # Binary floating point makes ceil(2.2 * 44100) one sample too large.
        self.assertEqual(sample_index(2.2, rate), 97020)
        left = span(2.0, 2.2, rate, 132300)
        right = span(2.2, 2.4, rate, 132300)
        self.assertEqual(left["end_sample"], right["start_sample"])
        source = np.arange(132300, dtype=np.int64) % 32767
        restored = np.concatenate(
            (
                source[left["start_sample"] : left["end_sample"]],
                source[right["start_sample"] : right["end_sample"]],
            )
        )
        np.testing.assert_array_equal(restored, source[88200:105840])
        self.assertEqual(len(restored), 17640)

    def test_half_sample_policy_and_invalid_inputs(self):
        self.assertEqual(sample_index(0.125, 4), 1)
        self.assertEqual(sample_index(0.375, 4), 2)
        for value in (float("nan"), float("inf"), -0.1):
            with self.assertRaises(ValueError):
                sample_index(value, 44100)
        with self.assertRaisesRegex(ValueError, "collapsed"):
            span(0, 0.000001, 44100, 44100)
        with self.assertRaises(ValueError):
            span(0, 2, 44100, 44100)

    def test_extraction_decodes_deterministically_and_leaves_source_unchanged(self):
        pcm = (np.arange(44100) % 32000).astype("<i2")
        original = pcm.tobytes()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            bounds = span(0.2, 0.55, 44100, len(pcm))
            first = export_clip(folder, "test.wav", pcm, 44100, bounds)
            second = export_clip(folder, "test.wav", pcm, 44100, bounds)
            self.assertEqual(first, second)
            actual, rate, _ = decode(folder / "test.wav")
            self.assertEqual(rate, 44100)
            np.testing.assert_array_equal(actual, pcm[8820:24255])
            self.assertEqual(pcm.tobytes(), original)
            with self.assertRaisesRegex(ValueError, "differs"):
                export_clip(folder, "test.wav", pcm, 44100, span(0.21, 0.55, 44100, len(pcm)))


class ToneBearingSpanTests(unittest.TestCase):
    def test_phone_families_preserve_complete_nucleus_and_coda(self):
        cases = [
            (["a˧˥"], 0),
            (["ʔ", "aj˥˩"], 1),  # noqa: RUF001 - IPA glottal stop
            (["j", "a˧˥", "ŋ"], 1),
            (["tʰ", "ow˧˥"], 1),
            (["kʰ", "w", "a˧˥", "ŋ"], 2),
            (["n", "a˨˩˦", "ɻ"], 1),
            (["ʂ", "ʐ̩˥˩"], 1),
            (["ts", "z̩"], 1),
            (["t", "ə"], 1),
            (["ɲ", "y˥", "n"], 1),
        ]
        for phones, first in cases:
            with self.subTest(phones=phones):
                row = row_for(phones)
                original = copy.deepcopy(row)
                actual = derive(row, 44100, 44100)
                self.assertTrue(actual["available"])
                final = actual["tone_bearing_pooling_span"]
                self.assertEqual(
                    final["start_sample"],
                    sample_index(row["aligned_phones"][first]["start"], 44100),
                )
                self.assertEqual(final["end_sample"], sample_index(row["end"], 44100))
                self.assertGreaterEqual(
                    final["start_sample"], actual["playback_read_unit"]["start_sample"]
                )
                self.assertEqual(row, original)
                self.assertEqual(actual["original_row_sha256"], digest(original))
                self.assertFalse(actual["ml_target_changed"])

    def test_unknown_missing_or_malformed_phones_are_unavailable_not_guessed(self):
        cases = [row_for(["q", "a˥"]), row_for(["n"]), row_for(["a˥", "i˥"]), row_for(["a˥", "t"])]
        gap = row_for(["n", "a˥"])
        gap["aligned_phones"][1]["start"] += 0.01
        cases.append(gap)
        for row in cases:
            result = derive(row, 44100, 44100)
            self.assertFalse(result["available"])
            self.assertIsNone(result["tone_bearing_pooling_span"])
            self.assertIn("unavailable", result["flags"])

    def test_no_neighbor_crossing_and_tone_not_used_for_geometry(self):
        left = row_for(["t", "ə"])
        right = row_for(["a˥", "ŋ"])
        for phone in right["aligned_phones"]:
            phone["start"] = round(phone["start"] + 0.2, 2)
            phone["end"] = round(phone["end"] + 0.2, 2)
        right.update(start=0.4, end=0.6)
        a, b = derive(left, 44100, 44100), derive(right, 44100, 44100)
        self.assertLessEqual(
            a["tone_bearing_pooling_span"]["end_sample"],
            b["tone_bearing_pooling_span"]["start_sample"],
        )
        changed = copy.deepcopy(left)
        changed.update(label="T1", corpus_pinyin="unrelated1", example_id="different")
        changed["aligned_phones"][-1]["phone"] = "ə˥"
        self.assertEqual(
            a["tone_bearing_pooling_span"],
            derive(changed, 44100, 44100)["tone_bearing_pooling_span"],
        )


class Round2ContractTests(unittest.TestCase):
    def packet(self, folder):
        original = row_for(["t", "ə"])
        s = derive(original, 44100, 44100)
        pcm = (np.arange(44100) % 32000).astype("<i2")
        media = {
            v: export_clip(folder, v + ".wav", pcm, 44100, s[key])
            for v, key in (
                ("target", "playback_read_unit"),
                ("final", "tone_bearing_pooling_span"),
                ("context", "context"),
            )
        }
        media["utterance"] = export_clip(
            folder, "utterance.wav", pcm, 44100, span(0, 1, 44100, 44100)
        )
        row = {
            "example_id": original["example_id"],
            "original": original,
            "spans": s,
            "playback": media,
        }
        item = {"item": "item-01", "row": row, "item_sha256": digest(row), "playback": media}
        payload = {
            "schema": SCHEMA,
            "items": [item],
            "decisions": list(WHOLE_DECISIONS),
            "final_decisions": list(FINAL_DECISIONS),
        }
        packet = {**payload, "packet_sha256": digest(payload)}
        write_json(folder / "packet.json", packet)
        return packet

    def test_manifest_and_html_deterministic_and_prior_verdicts_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            packet = self.packet(Path(tmp))
            self.assertEqual(render(packet), render(copy.deepcopy(packet)))
            page = render(packet).decode()
            for label in ("PLAY CONTEXT", "PLAY ORIGINAL TARGET", "PLAY TONE-BEARING TARGET"):
                self.assertIn(label, page)
            self.assertNotIn("human_review", page)
            self.assertNotIn("root_cause_classification", page)

    def test_dual_judgments_preserved_and_ingestion_never_releases(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            packet = self.packet(folder)
            review = {
                "example_id": "synthetic:unit",
                "item_sha256": packet["items"][0]["item_sha256"],
                "reviewer": "SYNTHETIC TEST ONLY",
                "reviewed_at": "2026-10-17T12:00:00Z",
                "decision": "START ISSUE",
                "final_decision": "PASS",
                "notes": "synthetic fuzzy onset",
                "heard_context_and_target": True,
                "heard_final": True,
            }
            raw = {"schema": SCHEMA, "packet_sha256": packet["packet_sha256"], "reviews": [review]}
            write_json(folder / "export.json", raw)
            result = ingest_round2(folder, folder / "export.json", folder / "ingested.jsonl")
            self.assertFalse(result["released"])
            saved = json.loads((folder / "ingested.jsonl").read_text())
            self.assertEqual(saved["decision"], "START ISSUE")
            self.assertEqual(saved["final_decision"], "PASS")
            review["heard_final"] = False
            (folder / "export.json").write_text(json.dumps(raw))
            with self.assertRaisesRegex(ValueError, "final_review_required"):
                ingest_round2(folder, folder / "export.json", folder / "bad.jsonl")
            self.assertFalse((folder / "bad.jsonl").exists())

    def test_changed_candidate_media_or_old_packet_cannot_clear_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.packet(folder)
            (folder / "final.wav").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "round2_media_changed"):
                ingest_round2(folder, folder / "missing.json", folder / "bad.jsonl")

    def test_all_pass_nested_round2_rows_ingest_without_changing_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            packet = self.packet(folder)
            original = (folder / "packet.json").read_bytes()
            item = packet["items"][0]
            review = {
                "example_id": item["row"]["example_id"], "item_sha256": item["item_sha256"],
                "reviewer": "SYNTHETIC TEST ONLY", "reviewed_at": "2026-10-17T12:00:00Z",
                "decision": "PASS", "final_decision": "PASS", "notes": "",
                "heard_context_and_target": True, "heard_final": True,
            }
            write_json(folder / "export.json", {
                "schema": SCHEMA, "packet_sha256": packet["packet_sha256"], "reviews": [review],
            })
            result = ingest_round2(folder, folder / "export.json", folder / "reviews.jsonl")
            self.assertEqual(result["final_decisions"], {"PASS": 1})
            self.assertFalse(result["released"])
            self.assertEqual((folder / "packet.json").read_bytes(), original)


if __name__ == "__main__":
    unittest.main()

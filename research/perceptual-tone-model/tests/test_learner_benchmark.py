"""Scientific boundary tests: discovery, provenance, alignment ownership and release gates."""

import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from perceptual_tone import learner_benchmark as lb
from perceptual_tone.aishell3_alignment import textgrid
from perceptual_tone.aishell3_boundaries import derive, span
from perceptual_tone.common import digest, file_hash, read_json, read_rows, write_json, write_rows


def wav(path, pcm):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        w.writeframes(pcm)


def record(phrase="我想买这个", intended=None):
    return {
        "alignment_transcript": phrase,
        "intended_phrase": intended,
        "actual_reading_hypothesis": None,
    }


class LearnerContracts(unittest.TestCase):
    def test_intended_reading_realization_and_outputs_are_distinct(self):
        r = record("我要去贵州", "我要去广州")
        r["actual_reading_hypothesis"] = "documented instruction 贵州; unverified realization"
        units = lb.tokens(r)
        self.assertEqual(units[3]["intended_pinyin"], "guang3")
        self.assertEqual(units[3]["alignment_pinyin"], "gui4")
        self.assertEqual(units[3]["intended_lexical_tone"], 3)
        self.assertEqual(units[3]["expected_surface_tone"], 3)
        self.assertEqual(units[3]["alignment_lexical_tone"], 4)
        self.assertTrue(
            all(
                u["model_prediction"] is None and u["human_perceptual_judgment"] is None
                for u in units
            )
        )

    def test_surface_neutral_and_chain_uncertainty_not_gold_labels(self):
        units = lb.tokens(record("我想买这个", "我想买这个"))
        self.assertEqual(units[-1]["intended_lexical_tone"], 4)
        self.assertEqual(units[-1]["expected_surface_tone"], 5)
        self.assertIsNone(units[0]["expected_surface_tone"])
        self.assertEqual(units[0]["surface_alternatives"], [2, 3])
        unknown = lb.tokens(record())
        self.assertTrue(all(u["intended_lexical_tone"] is None for u in unknown))
        self.assertEqual(
            lb.tokens(record("我要一个苹果", "我要一个苹果"))[2]["expected_surface_tone"], 2
        )

    def test_selection_cannot_use_model_predictions_or_historical_grade(self):
        config = read_json(lb.CONFIG)
        r = {
            "audio_exists": True,
            "alignment_transcript": "我",
            "role": "natural",
            "known_control": False,
            "names": ["synthetic-test"],
        }
        before = lb.selection(r, config)
        for prediction in [None, "T1", "T2", "T3", "T4"]:
            self.assertEqual(
                before,
                lb.selection(
                    {
                        **r,
                        "model_prediction": prediction,
                        "probabilities": [1, 0, 0, 0],
                        "deterministic": {"grade": "CLEAR_DIFFERENCE"},
                    },
                    config,
                ),
            )
        r["role"] = "unsuitable_unknown"
        self.assertEqual(lb.selection(r, config), "excluded")
        self.assertEqual(lb.role_for(["b8049b3eabc"], config)[0], "unsuitable_unknown")

    def test_discovery_deduplicates_original_copy_clip_and_manifests(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            var = root / "var"
            package = root / "research"
            canonical = var / "audio/account/canonical/take.wav"
            pcm = b"".join((i % 30000).to_bytes(2, "little") for i in range(16000))
            wav(canonical, pcm)
            original = var / "audio/account/original/upload.wav"
            wav(original, pcm)
            duplicate = var / "copies/copy.wav"
            wav(duplicate, pcm)
            clip = var / "clips/clip.wav"
            wav(clip, pcm[4000:8000])
            meta = var / "saved.json"
            write_json(
                meta,
                {
                    "canonical": {"sha256": file_hash(canonical)},
                    "original": {"storage_key": "account/original/upload.wav"},
                    "perception": {"transcript": "我想买"},
                    "intended_text": "我想买",
                    "analyses": [
                        {
                            "id": "analysis1",
                            "alignment_reference_text": "我想买",
                            "result": {
                                "syllables": [{"index": 0, "characters": "我", "lexical_tone": 3}]
                            },
                        }
                    ],
                },
            )
            config = {
                "natural": {"take": "explicit natural instruction"},
                "diagnostic": {},
                "excluded": {},
                "human_intent_unconfirmed": {},
                "supplemental_alignment_prefixes": [],
                "study_alignment_transcripts": {},
            }
            with (
                patch.object(lb, "VAR", var),
                patch.object(lb, "ROOT", root),
                patch.object(lb, "PACKAGE", package),
                patch.object(lb, "source_files", return_value=[meta]),
            ):
                rows = lb.discover(root / "out", config, study_dir=root / "empty-study")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["selection"], "proposed_benchmark")
            self.assertEqual(rows[0]["intended_phrase"], "我想买")
            self.assertEqual(rows[0]["historical_segmentation"][0]["analysis_id"], "analysis1")
            artifacts = read_rows(root / "out/audio-artifacts.jsonl")
            c = next(a for a in artifacts if a["path"].endswith("clip.wav"))
            self.assertEqual(c["relationship"], "exact_pcm_derivative")
            self.assertEqual(c["source_start_sample_16k"], 2000)
            self.assertTrue(all(a["recording_id"] == rows[0]["recording_id"] for a in artifacts))
            self.assertEqual(file_hash(canonical), rows[0]["audio"]["sha256"])

    def test_nucleus_coda_excludes_glide_and_preserves_half_open_samples(self):
        row = {
            "example_id": "synthetic",
            "start": 0.1,
            "end": 0.5,
            "aligned_phones": [
                {"phone": p, "start": a, "end": b}
                for p, a, b in [
                    ("ɕ", 0.1, 0.2),
                    ("j", 0.2, 0.3),
                    ("a˨˩˦", 0.3, 0.4),
                    ("ŋ", 0.4, 0.5),
                ]
            ],
        }
        result = derive(row, 16000, 16000)
        self.assertEqual(result["tone_bearing_pooling_span"]["start_sample"], 4800)
        self.assertEqual(result["owned_phone_indices"], [2, 3])
        self.assertEqual(result["context"]["start_sample"], 0)
        self.assertEqual(result["context"]["end_sample"], 12000)
        row["aligned_phones"][2]["start"] = 0.31
        self.assertFalse(derive(row, 16000, 16000)["available"])
        self.assertEqual(
            span(0.1, 0.3, 16000, 16000)["end_sample"], span(0.3, 0.5, 16000, 16000)["start_sample"]
        )

    def test_exact_crop_and_boundary_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            source = p / "source.wav"
            pcm = b"".join((i % 32000).to_bytes(2, "little") for i in range(16000))
            wav(source, pcm)
            interval = span(0.125, 0.375, 16000, 16000)
            a = lb.crop(source, interval, p / "crop.wav")
            with wave.open(str(p / "crop.wav")) as w:
                self.assertEqual(w.readframes(w.getnframes()), pcm[4000:12000])
            self.assertEqual(a["frames"], 4000)
            for a, b in [(-1, 0.1), (0.3, 0.2), (0, 1.1)]:
                with self.assertRaises(ValueError):
                    span(a, b, 16000, 16000)

    def test_import_rejects_wrong_unit_sequence(self):
        fixture = lb.PACKAGE / "tests/fixtures/aishell3"
        grids = list(fixture.rglob("*.TextGrid"))
        self.assertTrue(grids)
        text = grids[0].read_text()
        textgrid(text)
        u = {
            "utterance_id": "synthetic",
            "corpus": "test",
            "speaker_id": "test",
            "partition": "evaluation",
            "source_partition": "natural",
            "audio": {},
            "pcm_sha256": "x",
            "duration": 100,
            "transcript": "我",
            "transcript_provenance": {},
            "prosody_status": "unknown",
            "units": lb.tokens(record("我", "我")),
        }
        rows = lb.import_alignment(u, text, {}, {"alignment_log_likelihood": -20})
        self.assertIn("alignment_token_sequence_mismatch", rows[0]["exclusion_reasons"])
        self.assertIsNone(rows[0]["start"])

    def test_review_gate_rejects_missing_duplicate_wrong_packet_and_unheard(self):
        packet = {"packet_sha256": "abc", "items": [{"item_id": "Q001"}]}
        review = {
            "item_id": "Q001",
            "whole": "PASS",
            "tone": "PASS",
            "heard_all": True,
            "listened_views": ["context", "whole", "tone"],
            "reviewed_at": "2026-10-18",
            "notes": "",
        }
        data = {"packet_sha256": "abc", "reviewer": "SYNTHETIC TEST ONLY", "reviews": [review]}
        self.assertIn("Q001", lb.validate_reviews(packet, data))
        for change in [
            {"packet_sha256": "other"},
            {"reviews": []},
            {"reviews": [review, review]},
            {"reviews": [{**review, "heard_all": False}]},
            {"reviews": [{**review, "whole": "WRONG UNIT"}]},
        ]:
            with self.assertRaises(ValueError):
                lb.validate_reviews(packet, {**data, **change})
        data["reviews"][0].update(whole="START ISSUE", notes="synthetic note")
        self.assertEqual(lb.validate_reviews(packet, data)["Q001"]["whole"], "START ISSUE")

    def test_page_is_alignment_only_with_exact_choices(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "qa").mkdir()
            packet = {
                "items": [
                    {
                        "item_id": "Q001",
                        "example_id": "test",
                        "phrase": "我",
                        "index": 0,
                        "hanzi": "我",
                        "pinyin": "wo3",
                    }
                ],
                "whole_choices": lb.WHOLE,
                "tone_choices": lb.TONE,
            }
            lb.render_page(p, packet)
            text = (p / "qa/index.html").read_text()
            for label in ["PLAY CONTEXT", "PLAY WHOLE TARGET", "PLAY TONE-BEARING TARGET"]:
                self.assertIn(label, text)
            self.assertNotIn("model_prediction", text)
            self.assertNotIn("<option>T1</option>", text)
            self.assertEqual(text.count("<audio "), 3)

    def test_release_quarantines_bad_alignment_flags_and_unknown_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "qa").mkdir()
            (root / "aligned/jacob").mkdir(parents=True)
            grid = root / "aligned/jacob/source.TextGrid"
            grid.write_text("synthetic grid hash fixture; no real QA")
            rows = []
            items = []
            reviews = []
            for i in range(4):
                row = {
                    "example_id": f"synthetic:{i}",
                    "utterance_id": "source",
                    "flags": ["too_short"] if i == 1 else [],
                    "selection": "supplemental_provenance_quarantine"
                    if i == 2
                    else "proposed_benchmark",
                    "alignment_diagnostics": {"textgrid_sha256": file_hash(grid)},
                }
                rows.append(row)
                items.append({"item_id": f"Q{i}", "example_id": row["example_id"], "clips": {}})
                reviews.append(
                    {
                        "item_id": f"Q{i}",
                        "whole": "PASS",
                        "tone": "CLIPPED" if i == 3 else "PASS",
                        "notes": "synthetic test",
                        "heard_all": True,
                        "listened_views": ["context", "whole", "tone"],
                        "reviewed_at": "2026-10-18",
                    }
                )
            write_rows(root / "candidate-manifest.jsonl", rows)
            packet = {
                "candidate_manifest_sha256": file_hash(root / "candidate-manifest.jsonl"),
                "items": items,
            }
            packet["packet_sha256"] = digest(packet)
            write_json(root / "qa/packet.json", packet)
            write_json(root / "frozen-models.json", {"synthetic": True})
            for name in [
                "inventory.jsonl",
                "audio-artifacts.jsonl",
                "protocol.json",
                "selection-seal.json",
            ]:
                (root / name).write_text("{}\n")
            answers = root / "synthetic-answers.json"
            write_json(
                answers,
                {
                    "packet_sha256": packet["packet_sha256"],
                    "reviewer": "SYNTHETIC UNIT TEST ONLY",
                    "reviews": reviews,
                },
            )
            with patch.object(lb, "verify_inputs"):
                result = lb.release(root, answers, "synthetic-test")
                self.assertEqual(result["units"], 1)
                self.assertEqual(result["excluded"], 3)
                with self.assertRaises(FileExistsError):
                    lb.release(root, answers, "synthetic-test")
                grid.write_text("changed grid")
                with self.assertRaisesRegex(ValueError, "reviewed_alignment_changed"):
                    lb.release(root, answers, "synthetic-tamper")


if __name__ == "__main__":
    unittest.main()

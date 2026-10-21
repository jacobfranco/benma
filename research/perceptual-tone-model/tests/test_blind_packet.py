"""Blindness, immutable inputs, randomized presentation, and review contracts."""

import ast
import base64
import copy
import io
import json
import tempfile
import unittest
import wave
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from perceptual_tone import blind_packet as b
from perceptual_tone.common import digest, file_hash, read_json, read_rows


class BlindPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.learners, cls.pool, cls.failures = b.load_eligible()
        cls.controls = b.select_controls(cls.pool)
        cls.order = b.randomize(cls.learners, cls.controls)
        cls.selection = read_json(b.OUTPUT / "private/selection.json")
        cls.manifest = read_json(b.OUTPUT / "private/packet-manifest.json")
        cls.packet = {**cls.manifest, "packet_sha256": digest(cls.manifest)}
        cls.html = (b.OUTPUT / "qa/index.html").read_text()

    def synthetic(self):
        return {
            "schema": "benma-realized-tone-review-v1",
            "packet_version": b.VERSION,
            "packet_sha256": self.packet["packet_sha256"],
            "reviewer": "SYNTHETIC TEST ONLY",
            "reviews": [
                {
                    "annotation_id": p["annotation_id"],
                    "perceived_tone": "NEUTRAL",
                    "confidence": 3,
                    "usability": None,
                    "tone_bearing_heard": True,
                    "whole_target_heard": False,
                    "timestamp": "2026-10-19T20:00:00.000Z",
                }
                for p in self.order
            ],
        }

    def test_exact_learner_inclusion_and_exclusion(self):
        self.assertEqual(
            {r["unit_id"] for r in self.learners},
            {r["example_id"] for r in read_rows(b.LEARNER / "primary.jsonl")},
        )
        excluded = [
            r
            for r in read_rows(b.LEARNER / "all-units.jsonl")
            if r["quarantined"] or r["provenance_category"] != "PRIMARY_NATURAL_CANDIDATE"
        ]
        self.assertFalse(
            {r["example_id"] for r in excluded} & {r["unit_id"] for r in self.learners}
        )
        self.assertEqual(len(self.learners), 16)

    def test_control_eligibility_balance_source_independence(self):
        self.assertEqual(Counter(u["gold"] for u in self.controls), b.COUNTS)
        speakers = Counter(u["speaker_id"] for u in self.controls)
        self.assertEqual(len(speakers), 12)
        self.assertTrue(all(2 <= n <= 3 for n in speakers.values()))
        self.assertEqual(len({u["source_id"] for u in self.controls}), 28)
        self.assertEqual(len({u["mechanical"]["source_pcm_sha256"] for u in self.controls}), 28)
        self.assertEqual(len({u["mechanical"]["tone_pcm_sha256"] for u in self.controls}), 28)
        self.assertTrue(
            all(
                u["mechanical"]["periodic_frames"] > 0
                and u["mechanical"]["whole_peak_pcm16"] < 32760
                for u in self.controls
            )
        )
        split = read_json(b.NATIVE / "split.json")["assignments"]
        self.assertTrue(all(split[s] == "test" for s in speakers))
        self.assertFalse(set(speakers) & {u["speaker_id"] for u in self.learners})
        self.assertEqual(set(b.duration_bin(u) for u in self.controls), {"short", "medium", "long"})
        self.assertEqual(
            {u["position"] for u in self.controls}, {"utterance_edge", "utterance_medial"}
        )
        for tone in b.COUNTS:
            self.assertGreaterEqual(
                len({u["speaker_id"] for u in self.controls if u["gold"] == tone}), 4
            )

    def test_mechanical_checks_reject_wrong_ownership_silence_and_clipping(self):
        selected = self.controls[0]
        candidate = next(
            r
            for r in read_rows(b.NATIVE / "manifest.jsonl")
            if r["example_id"] == selected["unit_id"]
        )
        bad = copy.deepcopy(candidate["spans"])
        bad["tone_bearing_pooling_span"]["start_sample"] -= 1
        with self.assertRaisesRegex(ValueError, "ownership"):
            b.mechanical(candidate["original"], bad, control=True)
        with (
            patch.object(b, "periodic_frames", return_value=0),
            self.assertRaisesRegex(ValueError, "no_periodic"),
        ):
            b.mechanical(candidate["original"], candidate["spans"], control=True)
        pcm, rate, info = b.source_audio(
            candidate["original"]["audio"]["reference"], candidate["original"]["audio"]["sha256"]
        )
        clipped = pcm.copy()
        clipped[candidate["spans"]["playback_read_unit"]["start_sample"]] = 32767
        with (
            patch.object(b, "source_audio", return_value=(clipped, rate, info)),
            self.assertRaisesRegex(ValueError, "digital_clipping"),
        ):
            b.mechanical(candidate["original"], candidate["spans"], control=True)

    def test_randomization_opaque_ids_repeat_distance_and_source_mixing(self):
        self.assertEqual(self.order, self.selection["presentation_order"])
        self.assertEqual(self.order, b.randomize(self.learners, self.controls))
        self.assertNotEqual(self.order, b.randomize(self.learners, self.controls, b.SEED + 9))
        self.assertEqual(len({p["annotation_id"] for p in self.order}), 52)
        by_id = {p["annotation_id"]: p for p in self.order}
        units = {u["unit_id"]: u for u in self.learners + self.controls}
        copies = [p for p in self.order if p["duplicate_of"]]
        self.assertEqual(Counter(p["base_role"] for p in copies), {"learner": 3, "control": 5})
        self.assertEqual(
            {units[p["unit_id"]]["gold"] for p in copies if p["base_role"] == "control"},
            set(b.COUNTS),
        )
        for p in self.order:
            self.assertRegex(p["annotation_id"], r"^A[0-9a-f]{20}$")
            if p["duplicate_of"]:
                first = by_id[p["duplicate_of"]]
                self.assertEqual(p["unit_id"], first["unit_id"])
                self.assertGreaterEqual(p["order"] - first["order"], 15)
        for left, right in zip(self.order, self.order[1:], strict=False):
            self.assertNotEqual(
                units[left["unit_id"]]["source_id"], units[right["unit_id"]]["source_id"]
            )

    def test_duplicate_audio_is_identical_but_ids_are_not(self):
        public = {p["annotation_id"]: p for p in self.manifest["items"]}
        for p in self.order:
            if p["duplicate_of"]:
                self.assertEqual(
                    public[p["annotation_id"]]["audio"], public[p["duplicate_of"]]["audio"]
                )
                self.assertNotEqual(p["annotation_id"], p["duplicate_of"])

    def test_no_model_or_learner_label_dependent_selection(self):
        original_reader = b.read_rows

        def poisoned(path):
            rows = copy.deepcopy(original_reader(path))
            if path.name == "primary.jsonl" and path.parent == b.LEARNER:
                for row in rows:
                    for key in (
                        "expected_surface_tone",
                        "corpus_tone",
                        "intended_lexical_tone",
                        "model_prediction",
                        "expanded",
                        "pilot",
                        "deterministic",
                    ):
                        row[key] = "POISON_NOT_SELECTION_DATA"
            if path == b.NATIVE / "manifest.jsonl":
                for row in rows:
                    row["original"].update(
                        expanded="POISON", pilot="POISON", deterministic="POISON"
                    )
            return rows

        with patch.object(b, "read_rows", side_effect=poisoned):
            learners, pool, _ = b.load_eligible()
            self.assertEqual(b.randomize(learners, b.select_controls(pool)), self.order)
        tree = ast.parse(Path(b.__file__).read_text())
        calls = {
            n.func.attr
            for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        }
        self.assertFalse(calls & {"fit", "predict", "predict_proba", "partial_fit", "backward"})
        self.assertNotIn("predictions.jsonl", Path(b.__file__).read_text())
        self.assertNotIn("blind_key", Path(b.__file__).read_text())

    def test_visible_leakage_audit_and_mutation_rejection(self):
        self.assertEqual(b.leakage_audit(self.html, self.selection)["status"], "PASS")
        for injected in (
            "source_id",
            "SSB0287",
            "expected_surface_tone",
            "../private/answer-key.json",
        ):
            with self.assertRaises(ValueError):
                b.leakage_audit(self.html.replace("</main>", injected + "</main>"), self.selection)
        self.assertNotIn("fetch(", self.html)
        self.assertIn("connect-src 'none'", self.html)
        self.assertEqual([p.name for p in (b.OUTPUT / "qa").iterdir()], ["index.html"])

    def test_hidden_key_join_is_complete_and_does_not_touch_html(self):
        from perceptual_tone.blind_key import attach_key

        key = read_json(b.OUTPUT / "private/answer-key.json")
        self.assertEqual(len(key["items"]), 52)
        self.assertEqual(key["packet_sha256"], self.packet["packet_sha256"])
        self.assertFalse(key["analysis_performed"])
        for p in key["items"]:
            self.assertIsNone(p["realized_learner_tone"])
            if p["base_role"] == "learner":
                self.assertIsNotNone(p["expanded_model_result"])
                self.assertIsNotNone(p["pilot_model_result"])
                self.assertIsNone(p["native_control_gold_tone"])
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(FileNotFoundError):
            attach_key(Path(tmp))

    def test_export_round_trip_and_neutral_preservation(self):
        review = self.synthetic()
        self.assertEqual(b.validate_review(self.packet, review)["status"], "VALID_SCHEMA_ONLY")
        self.assertEqual(json.dumps(json.loads(json.dumps(review))), json.dumps(review))
        self.assertTrue(all(r["perceived_tone"] == "NEUTRAL" for r in review["reviews"]))
        for field, value in (
            ("perceived_tone", "T5"),
            ("confidence", 6),
            ("confidence", True),
            ("tone_bearing_heard", False),
            ("timestamp", "yesterday"),
            ("annotation_id", "source:leak"),
            ("usability", "GOOD"),
        ):
            bad = copy.deepcopy(review)
            bad["reviews"][0][field] = value
            with self.assertRaises(ValueError):
                b.validate_review(self.packet, bad)
        for field in ("source_id", "expected_surface_tone", "expanded"):
            bad = copy.deepcopy(review)
            bad["reviews"][0][field] = "leak"
            with self.assertRaises(ValueError):
                b.validate_review(self.packet, bad)
        bad = copy.deepcopy(review)
        bad["packet_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            b.validate_review(self.packet, bad)

    def test_audio_format_and_exact_delivery(self):
        self.assertEqual(
            b.public_manifest(self.learners + self.controls, self.order), self.manifest
        )
        for item in self.manifest["items"]:
            for uri in item["audio"].values():
                raw = base64.b64decode(uri.split(",")[1])
                with wave.open(io.BytesIO(raw)) as stream:
                    self.assertEqual(
                        (stream.getnchannels(), stream.getsampwidth(), stream.getframerate()),
                        (1, 2, 16000),
                    )
                    self.assertGreater(stream.getnframes(), 0)

    def test_packet_hash_reproduction_and_tamper_detection(self):
        seal = read_json(b.OUTPUT / "private/selection-seal.json")
        self.assertEqual(digest(self.manifest), seal["packet_sha256"])
        self.assertEqual(file_hash(b.OUTPUT / "private/selection.json"), seal["selection_sha256"])
        bad = copy.deepcopy(self.manifest)
        bad["items"].reverse()
        self.assertNotEqual(digest(bad), seal["packet_sha256"])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            b.build(path)
            self.assertEqual(
                (path / "qa/index.html").read_bytes(), (b.OUTPUT / "qa/index.html").read_bytes()
            )
            self.assertEqual(read_json(path / "private/selection.json"), self.selection)
            with self.assertRaisesRegex(ValueError, "immutable"):
                b.build(path)

    def test_production_and_all_preexisting_files_frozen(self):
        result = b.verify_preservation()
        self.assertEqual(result["baseline_hashes_unchanged"], 413)
        self.assertEqual(result["preexisting_files_unchanged"], 19012)


if __name__ == "__main__":
    unittest.main()

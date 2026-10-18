import copy
import sys
import tempfile
import unittest
from pathlib import Path

from perceptual_tone.aishell3_multispeaker import (
    make_split,
    split_summary,
    validate_adjudication,
    verify_packet,
)
from perceptual_tone.common import PACKAGE, digest, file_hash

sys.path.insert(0, str(PACKAGE / "scripts"))
from aishell3_multispeaker import release
from aishell3_multispeaker_train import verify_experiment_a
from perceptual_tone.aishell3_generalization_analysis import analyze


def fixture_rows():
    return [
        {
            "example_id": f"new-{s}-{i}",
            "speaker_id": f"SSB{s:04d}",
            "utterance_id": f"utt-{s}",
            "pcm_sha256": f"pcm-{s}",
            "label": f"T{i % 4 + 1}",
        }
        for s in range(100, 160)
        for i in range(64)
    ]


class MultiSpeakerTests(unittest.TestCase):
    def test_adjudication_preserves_enums_and_requires_every_issue(self):
        reviews = [
            {
                "example_id": "uncertain",
                "decision": "PASS",
                "final_decision": "CLIPPED",
                "notes": "too much at beginning",
            },
            {
                "example_id": "whole-only",
                "decision": "BOTH",
                "final_decision": "PASS",
                "notes": "whole target sounds wrong",
            },
        ]
        payload = {
            "systematic_bug_found": False,
            "model_predictions_inspected": False,
            "quarantined_example_ids": ["uncertain"],
            "items": [
                {
                    "example_id": r["example_id"],
                    "original_human_review": r,
                    "outcome": "QUARANTINE_UNIT"
                    if r["example_id"] == "uncertain"
                    else "PASS_AS_IS",
                    "neighbor_phones_in_pool": 0,
                    "exported_samples_exact": True,
                }
                for r in reviews
            ],
        }

        def seal(p):
            return {**p, "adjudication_sha256": digest(p)}

        self.assertEqual(
            validate_adjudication(seal(payload), reviews, {"uncertain", "whole-only"}),
            {"uncertain"},
        )
        changed = copy.deepcopy(payload)
        changed["items"][0]["original_human_review"]["final_decision"] = "CONTAMINATED"
        with self.assertRaisesRegex(ValueError, "changed_human_evidence"):
            validate_adjudication(seal(changed), reviews, {"uncertain", "whole-only"})
        missing = {**payload, "items": payload["items"][:1]}
        with self.assertRaisesRegex(ValueError, "every_human_issue"):
            validate_adjudication(seal(missing), reviews, {"uncertain", "whole-only"})
        with self.assertRaisesRegex(ValueError, "systematic_issue"):
            validate_adjudication(
                seal({**payload, "systematic_bug_found": True}),
                reviews,
                {"uncertain", "whole-only"},
            )

    def test_experiment_B_requires_frozen_A(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            self.assertRaisesRegex(ValueError, "before_any_experiment_B"),
        ):
            verify_experiment_a(Path(tmp))

    def test_per_speaker_and_cluster_bootstrap_denominators(self):
        import numpy as np

        rows = [
            {
                "example_id": f"{s}-{i}",
                "original": {
                    "label": f"T{i + 1}",
                    "speaker_id": s,
                    "following": None,
                    "utterance_id": s,
                    "index": i,
                },
            }
            for s in ("a", "b", "c")
            for i in range(4)
        ]
        truth = [r["original"]["label"] for r in rows]
        probs = np.tile(np.eye(4), (3, 1))
        result = analyze(rows, truth, probs, bootstrap_replicates=100)
        self.assertEqual(result["speaker_accuracy"]["mean"], 1)
        self.assertEqual(result["speaker_bootstrap"]["intervals"]["t3_recall"], [1, 1])
        self.assertEqual(result["t3_context"]["phrase_final"]["n"], 3)
        self.assertEqual(result["per_speaker"]["a"]["t3_correct"], 1)
        abstaining = analyze(rows, [None] * len(rows))
        self.assertEqual(abstaining["overall"]["abstentions"], 12)
        self.assertIsNone(abstaining["speaker_accuracy"]["mean"])

    def test_reproducible_diverse_split_independent_of_input_order(self):
        rows = fixture_rows()
        assigned, a = make_split(rows, {"SSB0001"}, 20261017)
        _, b = make_split(list(reversed(rows)), {"SSB0001"}, 20261017)
        self.assertEqual(a, b)
        self.assertEqual(
            [len(a["partitions"][p]["speakers"]) for p in ("train", "validation", "test")],
            [36, 12, 12],
        )
        self.assertEqual(a["concentration"]["test_units"], 768)
        self.assertEqual(a["concentration"]["test_t3"], 192)
        self.assertAlmostEqual(a["concentration"]["largest_test_speaker_share"], 1 / 12)
        changed = copy.deepcopy(rows)
        for r in changed:
            r["label"] = {"T1": "T2", "T2": "T3", "T3": "T4", "T4": "T1"}[r["label"]]
        self.assertEqual(make_split(changed, set(), 20261017)[1]["assignments"], a["assignments"])
        self.assertEqual(len(assigned), len(rows))

    def test_old_speaker_and_source_pcm_leakage_are_rejected(self):
        rows, info = make_split(fixture_rows(), set(), 20261017)
        with self.assertRaisesRegex(ValueError, "pilot_speaker"):
            split_summary(rows, info["assignments"], {rows[0]["speaker_id"]})
        train = next(r for r in rows if r["partition"] == "train")
        test = next(r for r in rows if r["partition"] == "test")
        test["pcm_sha256"] = train["pcm_sha256"]
        with self.assertRaisesRegex(ValueError, "split_leakage_pcm"):
            split_summary(rows, info["assignments"], set())

    def test_concentration_is_a_hard_gate(self):
        rows, info = make_split(fixture_rows(), set(), 20261017)
        test = next(r for r in rows if r["partition"] == "test")
        rows += [{**test, "example_id": f"extra-{i}"} for i in range(500)]
        with self.assertRaisesRegex(ValueError, "concentration"):
            split_summary(rows, info["assignments"], set())

    def test_packet_tamper_and_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            media = folder / "audio.wav"
            media.write_bytes(b"fixture")
            playback = {"target": {"reference": "audio.wav", "sha256": file_hash(media)}}
            row = {"example_id": "example", "playback": playback}
            payload = {"items": [{"row": row, "item_sha256": digest(row), "playback": playback}]}
            packet = {**payload, "packet_sha256": digest(payload)}
            verify_packet(packet, folder, file_hash)
            media.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "qa_media_changed"):
                verify_packet(packet, folder, file_hash)
            packet["items"][0]["item_sha256"] = "wrong"
            with self.assertRaisesRegex(ValueError, "qa_packet_hash_changed"):
                verify_packet(packet, folder, file_hash)

    def test_release_without_frozen_candidates_fails_before_model_operations(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(FileNotFoundError):
            release(Path(tmp), Path(tmp) / "nonexistent-decisions.json")


if __name__ == "__main__":
    unittest.main()

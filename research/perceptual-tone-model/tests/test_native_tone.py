"""Adversarial contracts for weak native-tone supervision; no synthetic scores."""

import copy
import importlib.util
import unittest

import numpy as np
from perceptual_tone.common import PACKAGE, read_rows
from perceptual_tone.features import vector
from perceptual_tone.native_labels import labels, strip_tone, t3_groups, tone_number
from perceptual_tone.native_protocol import (
    ambiguous_bases,
    baseline_prediction,
    metrics,
    model_input,
    speaker_partition,
    training_blockers,
    validate_split,
)


class NativeToneTests(unittest.TestCase):
    def test_transcript_reading_and_neutral(self):
        _, rows = labels("妈妈")
        self.assertEqual([r["pinyin"] for r in rows], ["ma1", "ma5"])
        self.assertEqual([r["label"] for r in rows], ["T1", "NEUTRAL"])
        self.assertEqual(tone_number("mǎi"), 3)
        self.assertEqual(tone_number("de5"), 0)
        with self.assertRaises(ValueError):
            tone_number("买")

    def test_surface_and_boundary_rules(self):
        cases = {
            "你好": ["T2", "T3"],
            "一杯": ["T4", "T1"],
            "不是": ["T2", "T4"],
            "第一": ["T4", "T1"],
            "一个": ["T2", None],
            "我，我": ["T3", "T3"],  # noqa: RUF001
            "买书": ["T3", "T1"],
            "买梨": ["T3", "T2"],
            "买菜": ["T3", "T4"],
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual([r["label"] for r in labels(text)[1]], expected)
        self.assertIn("sandhi_T3_to_T2", t3_groups(labels("你好")[1][0]))

    def test_uncertain_labels_are_not_lexical_fallbacks(self):
        rows = labels("我想买这个")[1]
        self.assertTrue(all(r["label"] is None for r in rows[:3]))
        self.assertIsNone(labels("行")[1][0]["label"])
        self.assertIsNone(labels("花儿")[1][0]["label"])
        self.assertIsNone(labels("一百")[1][0]["label"])
        self.assertIsNone(labels("看看")[1][1]["label"])
        self.assertIsNone(labels("看一看")[1][1]["label"])
        self.assertIsNone(labels("好不好")[1][1]["label"])

    def test_phonetic_identity_and_input_firewall(self):
        for value in ("mǎi", "mai3", "mai"):
            self.assertEqual(strip_tone(value), "mai")
        self.assertEqual(strip_tone("lǜ"), "lv")
        np.testing.assert_array_equal(
            model_input({"embedding": [1, 2], "phonetic_base": "mai"}), [1, 2]
        )
        for key in (
            "label",
            "lexical_tone",
            "surface_tone",
            "hanzi",
            "expected",
            "tone_marked_pinyin",
            "speaker_id",
        ):
            with self.assertRaises(ValueError):
                model_input({"embedding": [1], key: "T3"})
        for base in ("mai3", "mǎi", "买", "T3"):
            with self.assertRaises(ValueError):
                model_input({"embedding": [1], "phonetic_base": base})
        with self.assertRaises(ValueError):
            model_input({"embedding": [float("nan")]})

    def test_identity_vocabulary_uses_training_ambiguity(self):
        rows = [
            {"partition": "train", "phonetic_base": b, "label": t}
            for b, t in [("mai", "T3")] * 5 + [("mai", "T4")] * 5 + [("wo", "T3")] * 10
        ]
        self.assertEqual(ambiguous_bases(rows), ["mai"])
        with self.assertRaises(ValueError):
            ambiguous_bases([{**rows[0], "partition": "validation"}])

    def test_seeded_split_and_all_leakage_keys(self):
        speakers = list("abcdefghij")
        self.assertEqual(speaker_partition(speakers, 1), speaker_partition(speakers[::-1], 1))
        rows = [
            {
                "example_id": str(i),
                "speaker_id": str(i),
                "utterance_id": str(i),
                "pcm_sha256": str(i),
                "prompt_id": str(i),
                "partition": p,
            }
            for i, p in enumerate(("train", "validation", "test"))
        ]
        self.assertEqual(validate_split(rows), {"train": 1, "validation": 1, "test": 1})
        for key in ("speaker_id", "utterance_id", "pcm_sha256", "prompt_id"):
            changed = copy.deepcopy(rows)
            changed[1][key] = changed[0][key]
            with self.assertRaisesRegex(ValueError, key):
                validate_split(changed)
        changed = copy.deepcopy(rows)
        changed[0]["transcript"] = "你好。"
        changed[1]["transcript"] = "你好"
        with self.assertRaisesRegex(ValueError, "duplicate transcript"):
            validate_split(changed)

    def test_metrics_preserve_abstention_denominators(self):
        m = metrics(["T3", "T3", "T4", "NEUTRAL"], ["T4", None, "T4", None])
        self.assertEqual(m["coverage"], 0.5)
        self.assertEqual(m["accuracy_covered"], 0.5)
        self.assertEqual(m["correct_fraction_all"], 0.25)
        self.assertAlmostEqual(m["macro_f1_covered"], (2 / 3) / 5)
        self.assertEqual(m["T3_to_T4_all"], 0.5)
        self.assertEqual(m["confusion_covered_rows_truth_columns_prediction"][2][3], 1)
        self.assertEqual(m["abstentions_by_tone"]["NEUTRAL"], 1)
        self.assertIsNone(m["recall_covered"]["NEUTRAL"])
        self.assertIsNone(metrics([], [])["accuracy_covered"])
        with self.assertRaises(ValueError):
            metrics(["T3"], ["UNCLEAR"])

    def test_probability_order_and_confidence_one(self):
        m = metrics(["T1"], ["T1"], [[1, 0, 0, 0, 0]])
        self.assertEqual(m["reliability_bins"][-1]["n"], 1)
        with self.assertRaises(ValueError):
            metrics(["T1"], ["T3"], [[1, 0, 0, 0, 0]])

    def test_baseline_adapter_uses_acoustics_and_abstains(self):
        d = {
            "family_decision": "NUMBERED",
            "observed_family": "TONE_4",
            "winner": "TONE_3",
            "expected_surface_tone": 3,
            "color": "green",
        }
        self.assertEqual(baseline_prediction(d), "T4")
        for status in ("UNCLEAR", "UNAVAILABLE"):
            self.assertIsNone(baseline_prediction({**d, "family_decision": status}))
        self.assertIsNone(baseline_prediction(None))

    def test_f0_numeric_features_do_not_read_expected_labels(self):
        r = read_rows(PACKAGE / "stage0.baseline.jsonl")[0]
        original = vector(r, "benma")
        changed = copy.deepcopy(r)
        changed["expected"] = {"poison": "must_not_be_read"}
        changed["target"] = {"poison": "must_not_be_read"}
        changed["deterministic"]["resolved_expectation"] = None
        changed["deterministic"]["learner_grade"] = None
        changed["deterministic"]["acceptable_support"] = -999
        result = vector(changed, "benma")
        self.assertEqual(original[0], result[0])
        np.testing.assert_equal(original[1], result[1])

    def test_transcription_tier_cannot_be_used_as_alignment(self):
        spec = importlib.util.spec_from_file_location(
            "native_prepare", PACKAGE / "scripts/native_prepare.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with self.assertRaises(ValueError):
            module.word_intervals(
                'item [1]: name = "transcription" intervals [1]: xmin = 0 xmax = 1 text = "你"'
            )
        self.assertEqual(
            module.word_intervals(
                'item [1]: name = "words" intervals [1]: xmin = 0 xmax = 1 text = "你好"'
            ),
            [(0.0, 1.0, "你好")],
        )
        with self.assertRaises(ValueError):
            module.word_intervals(
                'item [1]: name = "words" intervals [1]: xmin = 0 xmax = 1e309 text = "你"'
            )

    def test_empty_qa_does_not_unlock_training(self):
        preflight = {
            "gates": {"alignment_audited": False},
            "config": {"phase_a_target_syllables": [500, 1000]},
        }
        blockers = training_blockers(preflight, [], [])
        self.assertIn("alignment_audited", blockers)
        self.assertIn("below_requested_phase_a_scale", blockers)
        self.assertIn("developer_audio_qa_missing_classes", blockers)


if __name__ == "__main__":
    unittest.main()

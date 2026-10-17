import copy
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace

import joblib
import numpy as np
from perceptual_tone.aishell3_embeddings import PAD, canonical_audio, input_audio
from perceptual_tone.aishell3_learning import (
    CLASSES,
    audio_contract,
    label_mutation_check,
    metric,
    pipeline,
    validate_audio_contract,
)
from perceptual_tone.common import PACKAGE, file_hash, write_json, write_rows
from perceptual_tone.embeddings import frame_centers

sys.path.insert(0, str(PACKAGE / "scripts"))
from aishell3_release import verify_release


class LearningTests(unittest.TestCase):
    def test_immutable_release_rejects_manifest_and_audio_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "audio.wav"
            source.write_bytes(b"source-audio-fixture")
            manifest = folder / "manifest.jsonl"
            write_rows(
                manifest,
                [{"original": {"audio": {"reference": str(source), "sha256": file_hash(source)}}}],
            )
            write_json(folder / "release.json", {"files": {"manifest.jsonl": file_hash(manifest)}})
            verify_release(folder)
            source.write_bytes(b"changed-audio")
            with self.assertRaisesRegex(ValueError, "source_audio_changed"):
                verify_release(folder)
            manifest.write_text("tampered manifest")
            with self.assertRaisesRegex(ValueError, "released_file_changed"):
                verify_release(folder)

    def test_annotations_do_not_enter_audio_contract(self):
        row = {
            "original": {
                "audio": {"reference": "a.wav", "sha256": "abc"},
                "start": 0.2,
                "end": 0.4,
                "aligned_phones": [{"phone": "a3"}],
                "label": "T3",
                "corpus_pinyin": "a3",
                "hanzi": "啊",
            },
            "spans": {
                "tone_bearing_pooling_span": {"start_seconds": 0.25, "end_seconds": 0.4},
                "context": {"start_seconds": 0, "end_seconds": 0.65},
            },
        }
        self.assertTrue(label_mutation_check(row))
        contract = audio_contract(row)
        validate_audio_contract(contract)
        for forbidden in ("label", "hanzi", "pinyin", "expected_tone", "acceptable_families"):
            with self.assertRaisesRegex(ValueError, "forbidden"):
                validate_audio_contract({**contract, forbidden: "T3"})
        broken = copy.deepcopy(contract)
        broken["pooling"] = [0.1, 0.4]
        with self.assertRaisesRegex(ValueError, "invalid"):
            validate_audio_contract(broken)

    def test_abstention_and_confusion_denominators(self):
        result = metric(["T1", "T2", "T3", "T3", "T3", "T4"], ["T1", None, "T3", "T4", "T2", "T4"])
        self.assertEqual(result["covered"], 5)
        self.assertEqual(result["accuracy"], 3 / 5)
        self.assertEqual(result["per_tone"]["T2"]["abstentions"], 1)
        self.assertEqual(result["T3_to_T4"], {"count": 1, "rate_all_T3": 1 / 3})
        self.assertEqual(result["T3_to_T2"]["count"], 1)
        self.assertEqual(result["per_tone"]["T3"]["recall"], 1 / 3)
        self.assertIsNone(metric(["T3"], [None])["accuracy"])

    def test_probability_bins_and_order(self):
        probs = np.array([[0.9, 0.04, 0.03, 0.03], [0.03, 0.03, 0.04, 0.9], [0.1, 0.2, 0.6, 0.1]])
        result = metric(["T1", "T3", "T3"], ["T1", "T4", "T3"], probs)
        self.assertEqual(result["high_confidence_errors"], 1)
        self.assertEqual(sum(b["n"] for b in result["confidence_bins"]), 3)
        with self.assertRaisesRegex(ValueError, "mismatch"):
            metric(["T1"] * 3, ["T1"] * 3, probs)

    def test_train_only_preprocessor_and_reload(self):
        train = np.array([[i, j, np.nan] for j in range(4) for i in range(8)], float)
        labels = np.repeat(CLASSES, 8)
        model = pipeline("logistic", 0.1).fit(train, labels)
        before = model[1].mean_.copy()
        probe = np.array([[1000, 1000, 3]], float)
        prob = model.predict_proba(probe)
        np.testing.assert_array_equal(model[1].mean_, before)
        self.assertEqual(before[0], 3.5)
        self.assertEqual(tuple(model.classes_), CLASSES)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.joblib"
            joblib.dump(model, path)
            np.testing.assert_array_equal(joblib.load(path).predict_proba(probe), prob)

    def test_short_edge_pool_has_frame_and_cache_checks_content(self):
        config = SimpleNamespace(
            conv_kernel=[10, 3, 3, 3, 3, 2, 2], conv_stride=[5, 2, 2, 2, 2, 2, 2]
        )
        for length in range(320, 8000, 160):
            count = (length + PAD * 2 - 400) // 320 + 1
            centers = frame_centers(config, count)
            self.assertTrue(((centers >= PAD + length - 320) & (centers < PAD + length)).any())
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "source.wav"
            with wave.open(str(source), "wb") as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(44100)
                f.writeframes(np.zeros(44100, dtype="<i2").tobytes())
            sha = file_hash(source)
            contract = {
                "audio_reference": str(source),
                "audio_sha256": sha,
                "read_unit": [0.2, 0.4],
                "pooling": [0.38, 0.4],
                "context": [0, 0.65],
            }
            audio, pool, path = input_audio(contract, "target", folder / "cache")
            self.assertEqual(len(audio), 3200 + PAD * 2)
            self.assertEqual(pool, (3080, 3400))
            self.assertEqual(canonical_audio(source, sha, folder / "cache"), path)
            path.write_bytes(b"corrupted")
            with self.assertRaisesRegex(ValueError, "corrupted"):
                canonical_audio(source, sha, folder / "cache")


if __name__ == "__main__":
    unittest.main()

"""Focused dev integration contracts; no fitting or native experiment reruns."""

import copy
import os
import tempfile
import time
import unittest
import wave
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
from perceptual_tone.common import PACKAGE, file_hash, read_json, read_rows
from perceptual_tone.dev_inference import (
    LearnedRecognizer,
    abstention,
    compare,
    require_dev,
    span_contract,
    validate_runtime_contract,
    verify_frozen,
)
from perceptual_tone.dev_runtime import DevRuntime, service
from perceptual_tone.learner_release import RELEASE, RUN
from perceptual_tone.learner_transfer import load_models, probabilities


def prediction(tone="T4"):
    p = {"T1": 0.02, "T2": 0.03, "T3": 0.04, "T4": 0.91}
    if tone != "T4":
        p[tone], p["T4"] = p["T4"], p[tone]
    return {"status": "ok", "prediction": tone, "confidence": 0.91, "probabilities": p}


class DevContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.audio = self.folder / "source.wav"
        with wave.open(str(self.audio), "wb") as stream:
            stream.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
            stream.writeframes(np.zeros(16000, dtype="<i2").tobytes())
        self.alignment = {
            "example_id": "unit",
            "index": 0,
            "start": 0.1,
            "end": 0.5,
            "exclusion_reasons": [],
            "audio": {"reference": str(self.audio), "sha256": file_hash(self.audio)},
            "aligned_phones": [
                {"phone": "m", "start": 0.1, "end": 0.2},
                {"phone": "aj˨˩˦", "start": 0.2, "end": 0.5},
            ],
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_frozen_hashes_and_all_413_baseline_files(self):
        self.assertEqual(verify_frozen()["baseline"]["verified_files"], 413)

    def test_changed_hash_refused_before_unpickling(self):
        with (
            patch("perceptual_tone.dev_inference.file_hash", return_value="tampered"),
            self.assertRaisesRegex(ValueError, "frozen_hash_mismatch"),
        ):
            verify_frozen()

    def test_span_uses_nucleus_coda_and_exact_context(self):
        contract, spans = span_contract(self.audio, self.alignment)
        self.assertEqual(contract["pooling"], [0.2, 0.5])
        self.assertEqual(contract["context"], [0, 0.75])
        self.assertEqual(spans["owned_phone_indices"], [1])

    def test_labels_cannot_influence_span_projection(self):
        first = span_contract(self.audio, self.alignment)
        changed = self.alignment | {
            "expected_surface_tone": 1,
            "hanzi": "错",
            "pinyin": "cuò",
            "grade": "pass",
        }
        self.assertEqual(first, span_contract(self.audio, changed))

    def test_expected_and_identity_rejected_at_encoder_boundary(self):
        contract, _ = span_contract(self.audio, self.alignment)
        for key in ("expected_tone", "hanzi", "pinyin", "intended_answer", "grade"):
            with (
                self.subTest(key=key),
                self.assertRaisesRegex(ValueError, "forbidden_encoder_input"),
            ):
                validate_runtime_contract(contract | {key: "secret"})

    def test_missing_rejected_and_unsupported_spans_abstain(self):
        examples = [
            None,
            self.alignment | {"exclusion_reasons": ["bad_ownership"]},
            self.alignment | {"aligned_phones": []},
            self.alignment | {"aligned_phones": [{"phone": "UNKNOWN", "start": 0.1, "end": 0.5}]},
        ]
        for row in examples:
            with self.subTest(row=row), self.assertRaises(ValueError):
                span_contract(self.audio, row)

    def test_short_nucleus_abstains_without_padding(self):
        row = copy.deepcopy(self.alignment)
        row["aligned_phones"][0]["end"] = 0.46
        row["aligned_phones"][1]["start"] = 0.46
        with self.assertRaisesRegex(ValueError, "too_little_material"):
            span_contract(self.audio, row)

    def test_nonfinite_and_outside_audio_contract(self):
        contract, _ = span_contract(self.audio, self.alignment)
        for context in ([0, float("inf")], [0, 2]):
            with self.assertRaises(ValueError):
                validate_runtime_contract(contract | {"context": context})

    def test_original_surface_precedence_neutral_and_unresolved(self):
        self.assertEqual(compare(4, prediction(), {}, {})["state"], "MATCH")
        for expected in (None, 0, 5):
            result = compare(expected, prediction(), {}, {})
            self.assertEqual(result["grade"], "unavailable")
            self.assertFalse(result["confident_error"])

    def test_concern_is_unthresholded_and_consensus_is_not_truth(self):
        result = compare(3, prediction(), prediction(), {"prediction": "T4"})
        self.assertEqual(result["state"], "MODEL_CONCERN_UNTHRESHOLDED")
        self.assertIsNone(result["confidence_threshold"])
        self.assertFalse(result["agreement_is_ground_truth"])
        self.assertFalse(result["confident_error"])

    def test_material_disagreement_does_not_override_expanded(self):
        result = compare(3, prediction(), prediction("T3"), {"prediction": "T3"})
        self.assertEqual(result["state"], "MODEL_DISAGREEMENT")
        self.assertEqual(result["grade"], "experimental_mismatch")
        self.assertIn("heard T4-like", result["interpretation"])

    def test_failed_model_never_makes_correction(self):
        result = compare(3, abstention("encoder_failure"), prediction(), {"prediction": "T4"})
        self.assertEqual(result["state"], "INSUFFICIENT_EVIDENCE")
        self.assertIsNone(result["explanation"])

    def test_explanation_requires_actual_support(self):
        base = {
            "prediction": "T4",
            "observed": {
                "decision": "NUMBERED",
                "evidence": "trustworthy",
                "strength": "full",
                "features": {"fall_st": 3.2},
            },
        }
        result = compare(3, prediction(), prediction(), base)
        self.assertTrue(result["specific_coaching_supported"])
        self.assertIn("3.20 semitones", result["explanation"])
        self.assertNotIn("recovery", result["explanation"])
        base["observed"]["evidence"] = "unavailable"
        result = compare(3, prediction(), prediction(), base)
        self.assertFalse(result["specific_coaching_supported"])
        self.assertIn("not clear enough", result["explanation"])

    def test_frozen_probability_reproduction_no_refit(self):
        matrix = np.load(RUN / "primary/features.npy", allow_pickle=False)[:2]
        actual = probabilities(load_models(read_json(RELEASE / "inference-config.json")), matrix)
        rows = read_rows(RUN / "primary/predictions.jsonl")[:2]
        for name, values in actual.items():
            np.testing.assert_allclose(
                values, [r[name]["probabilities"] for r in rows], atol=1e-12, rtol=0
            )

    def test_invalid_probabilities_are_rejected(self):
        for values in ([0.1] * 4, [float("nan"), 0, 0, 1], [-1, 0, 0, 2]):
            model = Mock()
            model.predict_proba.return_value = np.array([values])
            with self.assertRaisesRegex(ValueError, "invalid_frozen_probabilities"):
                probabilities({"expanded": model}, np.zeros((1, 768)))

    def recognizer(self):
        recognizer = LearnedRecognizer.__new__(LearnedRecognizer)
        recognizer.folder = self.folder
        recognizer.config = read_json(RELEASE / "inference-config.json")
        recognizer.encoder = Mock()
        recognizer.encoder.extract.return_value = (np.zeros((3, 768)), {"owned_frames": 15})
        model = Mock()
        model.predict_proba.return_value = np.array([[0.1, 0.2, 0.3, 0.4]])
        recognizer.models = {"expanded": model, "pilot": model}
        return recognizer

    def test_inference_schema_exact_audio_input_and_normalization(self):
        contract, _ = span_contract(self.audio, self.alignment)
        recognizer = self.recognizer()
        result = recognizer.infer(contract)
        recognizer.encoder.extract.assert_called_once_with(contract, "context")
        for name in ("expanded", "pilot"):
            row = result[name]
            self.assertEqual(row["prediction"], "T4")
            self.assertEqual(row["confidence"], 0.4)
            self.assertEqual(sum(row["probabilities"].values()), 1)
            self.assertEqual(row["span_metadata"], contract)
            self.assertEqual(row["layer"], 9)
            self.assertEqual(len(row["model_sha256"]), 64)

    def test_encoder_classifier_and_invalid_span_fail_closed(self):
        contract, _ = span_contract(self.audio, self.alignment)
        recognizer = self.recognizer()
        recognizer.encoder.extract.side_effect = RuntimeError("encoder unavailable")
        self.assertIn("encoder_failure", recognizer.infer(contract)["expanded"]["reason"])
        recognizer = self.recognizer()
        recognizer.models["expanded"].predict_proba.side_effect = ValueError("bad head")
        self.assertIn("classifier_failure", recognizer.infer(contract)["expanded"]["reason"])
        recognizer = self.recognizer()
        result = recognizer.infer(contract | {"expected_tone": 4})
        self.assertEqual(result["expanded"]["status"], "abstained")
        recognizer.encoder.extract.assert_not_called()

    def test_dev_opt_in_and_production_isolation(self):
        with self.assertRaises(ValueError):
            require_dev(False)
        with (
            patch.dict(os.environ, {"BENMA_ENVIRONMENT": "production"}),
            self.assertRaises(ValueError),
        ):
            require_dev(True)
        self.assertEqual(
            read_json(PACKAGE / "configs/dev-learned-lock.json")["confidence_threshold"], None
        )

    def test_smoke_expectations_preserve_existing_chain_and_chunk(self):
        result = service({"action": "expectations", "text": "我想买这个"})
        self.assertEqual(
            [s["expected_surface_tone"] for s in result["syllables"]], [None, None, None, 4, 0]
        )
        self.assertEqual(result["chunks"][0]["text"], "这个")

    def report(self, *, neutral=False, voiced=True, invalid=False, asr_mismatch=False):
        runtime = DevRuntime.__new__(DevRuntime)
        runtime.recognizer = Mock()
        runtime.recognizer.infer.return_value = {"expanded": prediction(), "pilot": prediction()}
        runtime.recognizer.performance.return_value = {}
        runtime.recognizer.verification = {"test": True}
        target = {
            "index": 0,
            "characters": "买",
            "pinyin": "mǎi",
            "pinyin_numeric": "mai3",
            "lexical_tone": 3,
            "expected_surface_tone": 0 if neutral else 3,
        }
        prepared = {
            "syllables": [target],
            "chunks": [],
            "asr": {"status": "available" if asr_mismatch else "unavailable", "transcript": "卖"},
        }
        baseline = {
            "unit": {
                "prediction": "T3",
                "segments": [[{"timestamp_seconds": 0.3, "normalized_semitones": 1}]]
                if voiced
                else [],
            }
        }
        destination = self.folder / "take"
        destination.mkdir()
        with (
            patch(
                "perceptual_tone.dev_runtime.deterministic", return_value=baseline
            ) as baseline_call,
            patch("perceptual_tone.dev_runtime.service", return_value=["mài"]),
        ):
            result = runtime.report(
                self.audio,
                prepared,
                [] if invalid else [self.alignment],
                destination,
                "买",
                time.perf_counter(),
                "test_fixture",
            )
        return result, runtime, baseline_call

    def test_deterministic_parallel_reporting_and_no_lexical_substitution(self):
        result, runtime, baseline = self.report()
        baseline.assert_called_once()
        runtime.recognizer.infer.assert_called_once()
        unit = result["units"][0]
        self.assertEqual(unit["target"]["characters"], "买")
        self.assertNotIn("hanzi", unit["heard"])
        self.assertEqual(unit["tone_realization_numeric"], "mai4")
        self.assertIn("not ASR", result["rendering_label"])
        self.assertEqual(unit["deterministic"]["prediction"], "T3")
        self.assertEqual(unit["comparison"]["state"], "MODEL_DISAGREEMENT")
        self.assertTrue((self.folder / "take/report.json").exists())

    def test_neutral_keeps_baseline_but_skips_numbered_inference(self):
        result, runtime, baseline = self.report(neutral=True)
        runtime.recognizer.infer.assert_not_called()
        baseline.assert_called_once()
        self.assertEqual(result["units"][0]["comparison"]["grade"], "unavailable")

    def test_no_voiced_support_skips_model(self):
        result, runtime, _ = self.report(voiced=False)
        runtime.recognizer.infer.assert_not_called()
        self.assertEqual(
            result["units"][0]["expanded"]["reason"], "no_voiced_support_in_tone_bearing_span"
        )

    def test_short_pool_is_playable_but_cannot_produce_a_correction(self):
        self.alignment["aligned_phones"][0]["end"] = 0.46
        self.alignment["aligned_phones"][1]["start"] = 0.46
        result, runtime, baseline = self.report()
        runtime.recognizer.infer.assert_not_called()
        baseline.assert_called_once()
        unit = result["units"][0]
        self.assertIn("too_little_material", unit["expanded"]["reason"])
        self.assertEqual(unit["spans"]["tone_bearing_pooling_span"]["start_seconds"], 0.46)
        self.assertEqual(set(unit["clips"]), {"whole", "tone", "context"})
        self.assertEqual(unit["comparison"]["grade"], "unavailable")

    def test_missing_alignment_reports_every_unit_without_model(self):
        result, runtime, baseline = self.report(invalid=True)
        runtime.recognizer.infer.assert_not_called()
        baseline.assert_not_called()
        self.assertEqual(len(result["units"]), 1)
        self.assertEqual(result["units"][0]["expanded"]["reason"], "missing_alignment")

    def test_asr_mismatch_preserves_evidence_and_abstains(self):
        result, runtime, baseline = self.report(asr_mismatch=True)
        runtime.recognizer.infer.assert_not_called()
        baseline.assert_called_once()
        self.assertEqual(
            result["units"][0]["expanded"]["reason"], "asr_prompt_mismatch_review_alignment"
        )


if __name__ == "__main__":
    unittest.main()

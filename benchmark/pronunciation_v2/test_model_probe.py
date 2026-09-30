"""Focused scientific controls, synthetic audio and tiny random encoder; no corpus fitting."""

import json
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

import model_probe as probe
import numpy as np
import torch
from features import (
    encode_waveforms,
    freeze,
    load_waveform,
    masked_mean,
    select_layers,
    state_digest,
)
from preflight import read_rows, sha256, write_csv
from remediate import BAD_ASSET, GROUPS, UNMARKED, clean_rows, disposition, validate_split
from transformers import Wav2Vec2Config, Wav2Vec2FeatureExtractor, Wav2Vec2Model


class RemediationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = read_rows(probe.CORPUS)
        cls.pages = {
            f"commons:{p['pageid']}": p
            for p in read_rows(
                Path.home() / ".cache/benma/benma-pronunciation-v2-pilot/candidate-evidence.jsonl"
            )
        }
        cls.decisions, cls.clean = clean_rows(cls.rows, cls.pages)

    def test_known_bad_and_singletons_excluded(self):
        self.assertEqual(len(self.clean), 495)
        self.assertNotIn(BAD_ASSET, {r["source_asset_id"] for r in self.clean})
        self.assertEqual({r["speaker_id"] for r in self.clean}, set(GROUPS))
        self.assertEqual(sum(r["partition"] == "train" for r in self.clean), 386)

    def test_unmarked_retained_only_with_explicit_primary_record(self):
        original = next(r for r in self.rows if r["source_asset_id"] == UNMARKED)
        self.assertTrue(disposition(original, self.pages[UNMARKED])[0])
        page = json.loads(json.dumps(self.pages[UNMARKED]))
        # An unmarked primary record must not be rescued by dictionary inference.
        text = page["revisions"][0]["slots"]["main"]["*"]
        page["revisions"][0]["slots"]["main"]["*"] = text.replace('"nǎ"', '"na"')
        self.assertFalse(disposition(original, page)[0])

    def test_no_leakage_and_invalid_tones_rejected(self):
        for key, value in [("partition", "test"), ("tone", 5), ("speaker_id", "singleton")]:
            rows = [dict(r) for r in self.clean]
            r = next(r for r in rows if r["partition"] == "train")
            r[key] = value
            with self.assertRaises(ValueError):
                validate_split(rows)

    def test_duplicate_audio_and_bad_asset_rejected(self):
        for key in ("audio_sha256", "decoded_pcm_sha256"):
            rows = [dict(r) for r in self.clean]
            rows[1][key] = rows[0][key]
            with self.assertRaises(ValueError):
                validate_split(rows)
        rows = [dict(r) for r in self.clean]
        rows[0]["source_asset_id"] = BAD_ASSET
        with self.assertRaises(ValueError):
            validate_split(rows)

    def test_deterministic_manifest(self):
        _, reversed_clean = clean_rows(list(reversed(self.rows)), self.pages)
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory) / "a.csv", Path(directory) / "b.csv"
            write_csv(a, self.clean)
            write_csv(b, reversed_clean)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertEqual(a.read_bytes(), (probe.OUTPUT / "split-manifest.csv").read_bytes())


class FeatureTests(unittest.TestCase):
    def test_audio_loading_resamples_stereo_to_16khz(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "audio.wav"
            values = np.sin(np.arange(48000) * 2 * np.pi * 200 / 48000) * 0.2
            stereo = np.stack([values, values], axis=1)
            with wave.open(str(p), "wb") as stream:
                stream.setnchannels(2)
                stream.setsampwidth(2)
                stream.setframerate(48000)
                stream.writeframes((stereo * 32767).astype("<i2").tobytes())
            waveform = load_waveform(p)
            self.assertEqual(waveform.shape, (16000,))
            # FFmpeg default stereo-to-mono uses equal-power mixing (+3 dB for identical channels).
            self.assertAlmostEqual(float(np.sqrt(np.mean(waveform**2))), 0.2, places=3)
            self.assertEqual(int(np.argmax(np.abs(np.fft.rfft(waveform)))), 200)

    def test_padding_excluded_even_when_hidden_padding_is_nonzero(self):
        hidden = torch.tensor([[[1.0, 3.0], [3.0, 5.0], [999.0, 999.0]]])
        mean = masked_mean(hidden, torch.tensor([[True, True, False]]))
        torch.testing.assert_close(mean, torch.tensor([[2.0, 4.0]]))
        with self.assertRaises(ValueError):
            masked_mean(hidden, torch.zeros(1, 3, dtype=torch.bool))

    def test_hidden_indices_and_frozen_deterministic_batches(self):
        torch.manual_seed(4)
        torch.set_num_threads(1)
        model = freeze(
            Wav2Vec2Model(
                Wav2Vec2Config(
                    hidden_size=16,
                    num_hidden_layers=8,
                    num_attention_heads=2,
                    intermediate_size=24,
                    conv_dim=(8, 8, 8),
                    conv_stride=(5, 2, 2),
                    conv_kernel=(10, 3, 3),
                    num_conv_pos_embeddings=8,
                    num_conv_pos_embedding_groups=2,
                    attn_implementation="eager",
                )
            )
        )
        processor = Wav2Vec2FeatureExtractor(return_attention_mask=False)
        waves = [np.random.default_rng(4).normal(size=n).astype(np.float32) for n in (1000, 1400)]
        before = state_digest(model)
        batched = encode_waveforms(model, processor, waves)
        individual = encode_waveforms(model, processor, waves[:1])
        for layer in (4, 6, 8):
            np.testing.assert_array_equal(batched[layer][0], individual[layer][0])
        self.assertEqual(before, state_digest(model))
        self.assertTrue(all(p.grad is None and not p.requires_grad for p in model.parameters()))
        observed = {}
        hooks = [
            model.encoder.layers[k - 1].register_forward_hook(
                lambda _m, _a, result, k=k: observed.update({k: result[0]})
            )
            for k in (4, 6, 8)
        ]
        with torch.inference_mode():
            states = model(torch.tensor(waves[0])[None], output_hidden_states=True).hidden_states
        for k, hidden in select_layers(states).items():
            torch.testing.assert_close(hidden, observed[k])
        for hook in hooks:
            hook.remove()
        with self.assertRaises(ValueError):
            select_layers(states, (0,))
        model.train()
        with self.assertRaises(ValueError):
            encode_waveforms(model, processor, waves)


class HeadAndFirewallTests(unittest.TestCase):
    def test_normalizer_uses_only_training(self):
        train = np.array([[0.0, 4.0], [2.0, 6.0]])
        scaler, scaled = probe.fit_head(train, [1, 2])
        np.testing.assert_array_equal(scaler.mean_, [1, 5])
        np.testing.assert_array_equal(scaled, [[-1, -1], [1, 1]])
        scaler.transform(np.array([[1e9, -1e9]]))
        np.testing.assert_array_equal(scaler.mean_, [1, 5])
        self.assertEqual(scaler.n_samples_seen_, 2)

    def test_selection_tie_break_and_fixed_metric(self):
        base = dict(macro_f1=0.5, balanced_accuracy=0.5, t2_t3_mean_recall=0.5, C=1.0, layer=6)
        self.assertGreater(probe.selection_key(dict(base, C=0.1)), probe.selection_key(base))
        self.assertGreater(
            probe.selection_key(dict(base, balanced_accuracy=0.6)), probe.selection_key(base)
        )
        self.assertEqual(probe.metrics([1, 2, 3, 4], [1, 2, 4, 4])["confusion_matrix"][2][3], 1)

    def test_test_cannot_open_without_lock(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(probe, "extract") as extract:
            with self.assertRaises(FileNotFoundError):
                probe.test(Path(directory), Path(directory))
            extract.assert_not_called()
            self.assertFalse((Path(directory) / "primary-test-opened.json").exists())

    def test_lock_detects_changed_split_and_receipt_is_exclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            split = output / "split-manifest.csv"
            split.write_text("original")
            (output / "experiment-config.locked.json").write_text(
                json.dumps({"split_manifest_sha256": sha256(split)})
            )
            split.write_text("modified")
            with self.assertRaisesRegex(ValueError, "Changed locked artifact"):
                probe.require_lock(output, output)
            receipt = output / "receipt.json"
            probe.exclusive_json(receipt, {"opened": True})
            with self.assertRaises(FileExistsError):
                probe.exclusive_json(receipt, {"opened": True})

    def test_saved_head_matches_multinomial_softmax(self):
        rng = np.random.default_rng(1)
        x = rng.normal(size=(40, 8))
        y = np.tile([1, 2, 3, 4], 10)
        scaler, train = probe.fit_head(x, y)
        model = probe.fit_classifier(train, y, 0.1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "head.npz"
            np.savez(
                path,
                mean=scaler.mean_,
                scale=scaler.scale_,
                coef=model.coef_,
                intercept=model.intercept_,
                classes=model.classes_,
            )
            np.testing.assert_allclose(
                probe.predict_head(path, x), model.predict_proba(train), atol=1e-12
            )


if __name__ == "__main__":
    unittest.main()

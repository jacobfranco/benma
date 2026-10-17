"""Frozen audio-only multi-layer embeddings with explicit frame-center ownership."""

import hashlib
import math
import wave
from pathlib import Path

import numpy as np
from scipy.signal import resample_poly

from .aishell3_boundaries import sample_index
from .aishell3_learning import validate_audio_contract
from .audio import read_audio
from .common import PACKAGE, digest, file_hash, read_json, runtime, write_json
from .embeddings import FrozenEncoder, frame_centers

VERSION = "aishell3-frozen-three-layer-mean-edgepad-v1"
LAYERS = (6, 9, 12)
PAD = 200  # 12.5 ms each side at 16 kHz; ensures short edge finals have frame centers.


def decode(path):
    pcm, rate, count = read_audio(str(path))
    return np.frombuffer(pcm, dtype="<i2"), rate, count


def canonical_audio(path, expected, folder):
    if file_hash(path) != expected:
        raise ValueError("audio_source_hash_changed")
    destination = Path(folder) / (expected + ".wav")
    if not destination.exists():
        pcm, rate, _ = decode(path)
        audio = (
            resample_poly(
                pcm.astype(np.float64) / 32768,
                16000 // math.gcd(rate, 16000),
                rate // math.gcd(rate, 16000),
            )
            if rate != 16000
            else pcm.astype(np.float64) / 32768
        )
        data = np.clip(np.rint(audio * 32768), -32768, 32767).astype("<i2")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(destination), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16000)
            w.writeframes(data.tobytes())
        write_json(
            destination.with_suffix(".json"),
            {
                "source_sha256": expected,
                "wav_sha256": file_hash(destination),
                "frames": len(data),
                "resampling": "scipy.resample_poly_full_utterance_then_pcm16_v1",
            },
        )
    metadata = read_json(destination.with_suffix(".json"))
    if metadata["wav_sha256"] != file_hash(destination) or metadata["source_sha256"] != expected:
        raise ValueError("canonical_cache_corrupted")
    return destination


def input_audio(contract, view, folder):
    validate_audio_contract(contract)
    if view not in ("target", "context"):
        raise ValueError("unknown_audio_view")
    path = canonical_audio(contract["audio_reference"], contract["audio_sha256"], folder)
    pcm, rate, _ = decode(path)
    start, end = contract["read_unit" if view == "target" else "context"]
    a, b = sample_index(start, rate), min(len(pcm), sample_index(end, rate))
    p, q = (sample_index(t, rate) - a + PAD for t in contract["pooling"])
    if not 0 <= a < b <= len(pcm) or not PAD <= p < q <= b - a + PAD:
        raise ValueError("invalid_resampled_pooling")
    values = np.pad(pcm[a:b].astype(np.float32) / 32768, (PAD, PAD))
    return values, (p, q), path


class Encoder:
    def __init__(self, name, cache, canonical):
        self.spec = read_json(PACKAGE / "configs/encoders.json")[name]
        self.base = FrozenEncoder(
            self.spec, {"view": "wide", "pooling": "target_mean", "device": "cpu", "threads": 4}
        )
        self.cache = Path(cache)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.canonical = Path(canonical)
        self.hits = 0
        self.misses = 0
        self.identity = {
            "version": VERSION,
            "encoder": self.spec,
            "weights": self.base.weights,
            "layers": list(LAYERS),
            "pooling": "tone_bearing_frame_center_mean",
            "edge_padding_samples_each_side": PAD,
            "runtime": runtime(),
            "threads": 4,
        }

    def extract(self, contract, view):
        import torch

        audio, target, _ = input_audio(contract, view, self.canonical)
        key = digest(
            {
                "identity": self.identity,
                "pcm": hashlib.sha256(audio.tobytes()).hexdigest(),
                "pool": target,
                "view": view,
            }
        )
        path = self.cache / (key + ".npy")
        meta = self.cache / (key + ".json")
        if path.exists() and meta.exists():
            record = read_json(meta)
            if file_hash(path) != record["sha256"]:
                raise ValueError("embedding_cache_corrupted")
            result = np.load(path, allow_pickle=False)
            self.hits += 1
        else:
            if path.exists() or meta.exists():
                raise ValueError("incomplete_embedding_cache")
            if self.base.model is None:
                self.base._load()
            inputs = self.base.processor(audio, sampling_rate=16000, return_tensors="pt")
            with torch.inference_mode():
                hidden = self.base.model(**inputs, output_hidden_states=True).hidden_states
                centers = frame_centers(self.base.model.config, hidden[6].shape[1])
                mask = (centers >= target[0]) & (centers < target[1])
                if not mask.any():
                    raise ValueError("no_frame_centers_in_pool")
                result = np.stack(
                    [hidden[layer][0, mask].mean(0).cpu().numpy() for layer in LAYERS]
                ).astype(np.float32)
            with path.open("xb") as f:
                np.save(f, result, allow_pickle=False)
            record = {
                "key": key,
                "sha256": file_hash(path),
                "owned_frames": int(mask.sum()),
                "target_samples": list(target),
                "view": view,
                "identity": self.identity,
            }
            write_json(meta, record)
            self.misses += 1
        if result.shape != (3, 768) or not np.isfinite(result).all():
            raise ValueError("bad_embedding_vector")
        return result, record

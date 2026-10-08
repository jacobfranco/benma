"""Pinned offline RMVPE research adapter. No production filters or lexical inputs.

Uses the unmodified RVC implementation and one checkpoint; no automatic download.
The native 0.03 threshold is part of raw output. Full salience and the ungated
native decode are saved separately so threshold views never require inference.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

from benchmark.pronunciation_v2.f0_foundation import PitchFrame, UtterancePitchTrack, read_audio

ROOT = Path(__file__).resolve().parents[2] / "services/api/var/f0-foundation/rmvpe"
SOURCE_COMMIT = "81eed5e8f68b6bed1789f682fe78cdd324495afc"
SOURCE_HASHES = {
    "infer/rmvpe.py": "074171aec63e4b68f04d8691c62af50a1d99b9bc6dc56c4d6749fad4ba64853a",
    "tools/cuda_graph.py": "e3b4ce4fc8a33a3a921e70f78ce6965440c770d79d3ce71fb9f215db3a2db1a2",
}
MODEL_HASH = "6d62215f4306e3ca278246188607209f09af3dc77ed4232efdd069798c4ec193"
NATIVE_THRESHOLD = 0.03
SWEEP_THRESHOLDS = (0.01, 0.02, 0.03, 0.04, 0.05)
VIEW_THRESHOLD = 0.05  # Predeclared endpoint for the optional removal-only viewer view.
BIN_CENTS = 20 * np.arange(360) + 1997.3794084376191
BIN_HZ = 10 * 2 ** (BIN_CENTS / 1200)


@lru_cache(maxsize=1)
def load_model():
    """CPU float32, one thread, fixed weights; reject substituted source/checkpoint."""
    import torch

    source = Path(os.environ.get("BENMA_RMVPE_SOURCE", ROOT / "vendor/rvc"))
    checkpoint = Path(os.environ.get("BENMA_RMVPE_MODEL", ROOT / "vendor/rmvpe.pt"))
    for relative, expected in SOURCE_HASHES.items():
        if hashlib.sha256((source / relative).read_bytes()).hexdigest() != expected:
            raise ValueError(f"RMVPE source hash mismatch: {relative}")
    if hashlib.sha256(checkpoint.read_bytes()).hexdigest() != MODEL_HASH:
        raise ValueError("RMVPE checkpoint hash mismatch")
    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != 1:
        torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    # The upstream module imports its own tools.cuda_graph helper (CPU uses eager).
    sys.path.insert(0, str(source))
    spec = importlib.util.spec_from_file_location(
        "benma_research_rmvpe_vendor", source / "infer/rmvpe.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Initialization draws random weights before loading all fixed weights. Preserve
    # caller state; inference uses eval(), so dropout and training randomness are off.
    with torch.random.fork_rng(devices=[]):
        model = module.RMVPE(str(checkpoint), is_half=False, device="cpu")
    return model


def confidence_view(track: UtterancePitchTrack, threshold: float = VIEW_THRESHOLD) -> np.ndarray:
    """Removal-only view of native F0; no energy, duration, range or pitch repair."""
    if threshold < NATIVE_THRESHOLD:
        raise ValueError("lower thresholds require the saved ungated native decode")
    _, hz, confidence = track.arrays()
    return np.where(confidence > threshold, hz, np.nan)


def extract(path: Path, *, activations_path: Path | None = None) -> UtterancePitchTrack:
    import librosa
    import torch

    model = load_model()
    audio, rate = read_audio(path)
    # Matches upstream example: librosa's default soxr_hq resampling, no gain scaling.
    samples = audio.astype(np.float32)
    if rate != 16000:
        samples = librosa.resample(samples, orig_sr=rate, target_sr=16000, res_type="soxr_hq")
    with torch.inference_mode():
        mel = model.extract_mel(samples, center=True)
        salience = model.mel2hidden(mel).squeeze(0).cpu().numpy()
    hz = model.decode(salience, thred=NATIVE_THRESHOLD)
    confidence = salience.max(axis=1)
    times = np.arange(len(hz), dtype=float) * 0.01
    if activations_path is not None:
        np.savez_compressed(
            activations_path,
            salience=salience,
            times=times,
            native_f0_hz=hz,
            ungated_f0_hz=model.decode(salience, thred=0.0),
            confidence=confidence,
            bin_hz=BIN_HZ,
        )
    top = np.argsort(salience, axis=1)[:, -5:][:, ::-1]
    frames = tuple(
        PitchFrame(
            float(t),
            float(h) if h > 0 else None,
            float(c),
            bool(h > 0),
            tuple((float(BIN_HZ[b]), float(salience[i, b])) for b in top[i]),
        )
        for i, (t, h, c) in enumerate(zip(times, hz, confidence, strict=True))
    )
    return UtterancePitchTrack(
        hashlib.sha256(path.read_bytes()).hexdigest(),
        "rmvpe",
        rate,
        len(audio) / rate,
        0.01,
        "max_native_sigmoid_salience_not_calibrated_speech_probability",
        {
            "source_repository": "RVC-Project/Retrieval-based-Voice-Conversion-WebUI",
            "source_commit": SOURCE_COMMIT,
            "source_hashes": SOURCE_HASHES,
            "model_sha256": MODEL_HASH,
            "device": "cpu",
            "dtype": "float32",
            "threads": 1,
            "torch": torch.__version__,
            "librosa": librosa.__version__,
            "input_rate_hz": 16000,
            "resample": "librosa_soxr_hq_when_needed",
            "hop_length": 160,
            "fft_length": 1024,
            "window": "hann_centered_reflect",
            "mel_channels": 128,
            "mel_range_hz": [30, 8000],
            "htk_mel": True,
            "mel_log_clamp": 1e-5,
            "network_time_padding": "zero_to_multiple_of_32_then_trim",
            "decoder": "native_local_average_argmax_plus_minus_4_bins",
            "voiced_if_max_salience_gt": NATIVE_THRESHOLD,
            "bin_range_hz": [float(BIN_HZ[0]), float(BIN_HZ[-1])],
            "bins": 360,
            "bin_step_cents": 20,
            "pitch_range_mask": None,
            "whole_utterance": True,
            "eval_mode": True,
            "deterministic_algorithms": True,
        },
        frames,
    )

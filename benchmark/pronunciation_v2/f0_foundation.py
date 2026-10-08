"""Offline, character-free F0 research. No production imports, network, or lexical inputs.

Dependencies live in an isolated research environment; see the dated report.
Native tracker decisions are immutable. Cleanup and alignment are separate views.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import wave
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

ORIGINAL_TRACKERS = ("praat_ac", "praat_cc", "pyin", "harvest", "crepe_full")
TRACKERS = (*ORIGINAL_TRACKERS, "rmvpe")
PRAAT_PARAMETERS = {
    "pitch_floor": 50.0,
    "pitch_ceiling": 550.0,
    "time_step": 0.01,
    "octave_jump_cost": 0.5,
    "octave_cost": 0.01,
    "voiced_unvoiced_cost": 0.14,
    "silence_threshold": 0.03,
    "max_number_of_candidates": 15,
    "very_accurate": False,
    "voicing_threshold": 0.45,
}


@dataclasses.dataclass(frozen=True)
class PitchFrame:
    timestamp_seconds: float
    f0_hz: float | None
    confidence: float | None
    native_voiced: bool | None
    candidates: tuple[tuple[float, float], ...] = ()


@dataclasses.dataclass(frozen=True)
class UtterancePitchTrack:
    audio_sha256: str
    tracker: str
    sample_rate_hz: int
    duration_seconds: float
    frame_cadence_seconds: float
    confidence_kind: str
    configuration: dict[str, Any]
    frames: tuple[PitchFrame, ...]

    def canonical_bytes(self) -> bytes:
        """Stable evidence serialization: no runtime, transcript, target, or path."""
        return json.dumps(
            dataclasses.asdict(self), sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()

    def arrays(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        return tuple(
            np.array([getattr(f, key) for f in self.frames], dtype=float)
            for key in ("timestamp_seconds", "f0_hz", "confidence")
        )


def read_audio(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path)) as stream:
        if stream.getnchannels() != 1 or stream.getsampwidth() != 2:
            raise ValueError("research input must be mono PCM16 WAV")
        rate = stream.getframerate()
        audio = np.frombuffer(stream.readframes(stream.getnframes()), "<i2").astype(float) / 32768
    if len(audio) == 0:
        raise ValueError("empty audio")
    return audio, rate


def write_audio(path: Path, audio: np.ndarray, rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(rate)
        stream.writeframes(np.clip(np.rint(audio * 32768), -32768, 32767).astype("<i2").tobytes())


def extract_utterance_pitch(
    path: Path, tracker: str, *, activations_path: Path | None = None
) -> UtterancePitchTrack:
    """One waveform, one fixed estimator. Metadata is deliberately not accepted."""
    if tracker == "rmvpe":
        from benchmark.pronunciation_v2.f0_foundation_rmvpe import extract

        return extract(path, activations_path=activations_path)
    audio, rate = read_audio(path)
    candidates: list[tuple[tuple[float, float], ...]] = []
    if tracker in {"praat_ac", "praat_cc"}:
        import parselmouth

        sound = parselmouth.Sound(audio, sampling_frequency=rate)
        pitch = getattr(sound, "to_pitch_ac" if tracker == "praat_ac" else "to_pitch_cc")(
            **PRAAT_PARAMETERS
        )
        times = pitch.xs()
        hz = pitch.selected_array["frequency"].copy()
        confidence = pitch.selected_array["strength"].copy()
        voiced = hz > 0
        hz[~voiced] = np.nan
        candidates = [
            tuple((float(c.frequency), float(c.strength)) for c in f.candidates) for f in pitch
        ]
        config = {
            **PRAAT_PARAMETERS,
            "parselmouth": parselmouth.VERSION,
            "praat": parselmouth.PRAAT_VERSION,
        }
        confidence_kind = "native_candidate_strength_not_speech_probability"
    elif tracker == "pyin":
        import librosa

        # Fixed 64-ms window at every input rate, >3 periods at the 50-Hz floor.
        config = {
            "fmin": 50.0,
            "fmax": 550.0,
            "frame_length": round(rate * 0.064),
            "hop_length": round(rate * 0.01),
            "center": True,
            "librosa": librosa.__version__,
            "other_parameters": "0.11.0 defaults",
        }
        hz, voiced, confidence = librosa.pyin(
            audio,
            sr=rate,
            **{k: config[k] for k in ("fmin", "fmax", "frame_length", "hop_length", "center")},
        )
        times = np.arange(len(hz)) * config["hop_length"] / rate
        confidence_kind = "native_voiced_probability"
    elif tracker == "harvest":
        import pyworld

        config = {
            "f0_floor": 50.0,
            "f0_ceil": 550.0,
            "frame_period": 10.0,
            "pyworld": pyworld.__version__,
        }
        hz, times = pyworld.harvest(
            audio, rate, **{k: config[k] for k in ("f0_floor", "f0_ceil", "frame_period")}
        )
        voiced = hz > 0
        hz[~voiced] = np.nan
        confidence = np.full(len(hz), np.nan)
        confidence_kind = "unavailable"
    elif tracker == "crepe_full":
        import torch
        import torchcrepe

        config = {
            "capacity": "full",
            "fmin": 50.0,
            "fmax": 550.0,
            "hop_seconds": 0.01,
            "inference_batch_frames": 128,
            "decoder": "native_viterbi_whole_utterance",
            "pad": True,
            "dither_seed": 20261005,
            "torchcrepe": "0.0.24",
            "source_revision": "19e2ec3d494c0797a5ff2a11408ec5838fba6681",
            "model_sha256": "133225604dedd2e4005f8bbd1bd0a2ec073ba8b7a6cd31ff6d5edbbfa3539986",
        }
        tensor = torch.tensor(audio, dtype=torch.float32)[None]
        with torch.inference_mode():
            batches = [
                torchcrepe.infer(frames, model="full", device="cpu")
                for frames in torchcrepe.preprocess(
                    tensor, rate, round(rate * 0.01), batch_size=128, device="cpu", pad=True
                )
            ]
            activations = torch.cat(batches, dim=0)
            if activations_path is not None:
                np.savez_compressed(activations_path, activations=activations.numpy())
            # Chunk only independent inference, never the temporal decoder.
            # Upstream conversion dithers bin frequencies with NumPy randomness.
            # Pin and restore that RNG; no tracker decisions are repaired.
            state = np.random.get_state()
            np.random.seed(20261005)
            try:
                pitch, periodicity = torchcrepe.postprocess(
                    activations.T[None].clone(),
                    50.0,
                    550.0,
                    decoder=torchcrepe.decode.viterbi,
                    return_periodicity=True,
                )
            finally:
                np.random.set_state(state)
        hz, confidence = pitch[0].numpy(), periodicity[0].numpy()
        times = np.arange(len(hz)) * 0.01
        voiced = [None] * len(hz)  # CREPE has no native voiced/unvoiced decision.
        confidence_kind = "native_periodicity_no_voicing_mask"
        top = torch.topk(activations, 5, dim=1)
        frequencies = 10 * 2 ** ((20 * top.indices.numpy() + 1997.3794084376191) / 1200)
        candidates = [
            tuple(zip(f.tolist(), p.tolist(), strict=True))
            for f, p in zip(frequencies, top.values.numpy(), strict=True)
        ]
    else:
        raise ValueError(f"unknown tracker: {tracker}")
    frames = tuple(
        PitchFrame(
            float(t),
            float(h) if np.isfinite(h) else None,
            float(c) if np.isfinite(c) else None,
            bool(v) if v is not None else None,
            candidates[i] if candidates else (),
        )
        for i, (t, h, c, v) in enumerate(zip(times, hz, confidence, voiced, strict=True))
    )
    return UtterancePitchTrack(
        hashlib.sha256(path.read_bytes()).hexdigest(),
        tracker,
        rate,
        len(audio) / rate,
        float(np.median(np.diff(times))),
        confidence_kind,
        config,
        frames,
    )


def track_record(record: Mapping[str, Any], tracker: str) -> UtterancePitchTrack:
    """Research metadata boundary. Only audio_path is forwarded to extraction."""
    return extract_utterance_pitch(Path(record["audio_path"]), tracker)


def frame_rms(audio: np.ndarray, rate: int, times: np.ndarray) -> np.ndarray:
    width = round(0.032 * rate)
    return np.array(
        [
            np.sqrt(
                np.mean(
                    audio[
                        max(0, round(t * rate) - width) : min(len(audio), round(t * rate) + width)
                    ]
                    ** 2
                )
            )
            for t in times
        ]
    )


def runs(mask: np.ndarray) -> list[tuple[int, int]]:
    edges = np.diff(np.r_[False, mask, False].astype(int))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1), strict=True))


def minimal_cleanup(track: UtterancePitchTrack, audio: np.ndarray) -> np.ndarray:
    """One predeclared generic view: confidence, -60 dBFS, <30-ms islands.

    Native confidences are not calibrated across algorithms. Praat already uses .45;
    pYIN .1 is a conservative low-confidence rejection; CREPE .21 is upstream's
    clean-speech example. Harvest exposes no confidence. No gap filling or F0 change.
    """
    if track.tracker == "rmvpe":
        from benchmark.pronunciation_v2.f0_foundation_rmvpe import confidence_view

        return confidence_view(track)
    times, hz, confidence = track.arrays()
    thresholds = {"praat_ac": 0.45, "praat_cc": 0.45, "pyin": 0.1, "crepe_full": 0.21}
    keep = np.isfinite(hz) & (frame_rms(audio, track.sample_rate_hz, times) >= 0.001)
    if track.tracker in thresholds:
        keep &= confidence >= thresholds[track.tracker]
    for start, end in runs(keep):
        if (end - start) * track.frame_cadence_seconds < 0.03 - 1e-9:
            keep[start:end] = False
    return np.where(keep, hz, np.nan)


def sample_nearest(times: np.ndarray, values: np.ndarray, query: np.ndarray) -> np.ndarray:
    """Nearest native frame within half a hop; never bridge a missing frame."""
    if not len(times):
        return np.full(len(query), np.nan)
    right = np.clip(np.searchsorted(times, query), 0, len(times) - 1)
    left = np.maximum(0, right - 1)
    index = np.where(abs(times[left] - query) <= abs(times[right] - query), left, right)
    hop = np.median(np.diff(times)) if len(times) > 1 else 0.01
    return np.where(abs(times[index] - query) <= hop / 2 + 1e-7, values[index], np.nan)


def basic_metrics(
    times: np.ndarray,
    hz: np.ndarray,
    confidence: np.ndarray,
    *,
    cadence_seconds: float | None = None,
) -> dict[str, Any]:
    voiced = np.isfinite(hz)
    hop = cadence_seconds or (float(np.median(np.diff(times))) if len(times) > 1 else 0.01)
    indices = np.flatnonzero(voiced)
    islands = []
    for index in indices:
        if islands and index == islands[-1][1] and times[index] - times[index - 1] <= 1.51 * hop:
            islands[-1] = (islands[-1][0], index + 1)
        else:
            islands.append((index, index + 1))
    steps = abs(12 * np.diff(np.log2(hz[voiced])))
    delta = np.diff(times[voiced])
    adjacent = steps[delta <= 1.51 * hop]
    nearby = steps[delta <= 0.12 + 1e-7]
    conf = confidence[voiced & np.isfinite(confidence)]
    return {
        "frames": len(times),
        "emitted_frames": int(voiced.sum()),
        "coverage": float(voiced.mean()) if len(hz) else None,
        "median_hz": float(np.median(hz[voiced])) if len(indices) else None,
        "min_hz": float(np.min(hz[voiced])) if len(indices) else None,
        "max_hz": float(np.max(hz[voiced])) if len(indices) else None,
        "islands": len(islands),
        "short_islands": int(sum((b - a) * hop < 0.04 - 1e-8 for a, b in islands)),
        "longest_run_seconds": float(max(((b - a) * hop for a, b in islands), default=0)),
        "jumps_gt6": int((adjacent > 6).sum()),
        "jumps_gt9": int((adjacent > 9).sum()),
        "jumps_gt12": int((adjacent > 12).sum()),
        "nearby_jumps_gt9": int((nearby > 9).sum()),
        "adjacent_pairs": len(adjacent),
        "confidence_median": float(np.median(conf)) if len(conf) else None,
        "confidence_max": float(np.max(conf)) if len(conf) else None,
    }


def known_f0_metrics(times: np.ndarray, hz: np.ndarray, truth: dict[str, Any]) -> dict[str, Any]:
    source_t = np.asarray(truth["times"])
    target = sample_nearest(source_t, np.asarray(truth["f0_hz"], dtype=float), times)
    # Exclude 80 ms around known boundaries from steady-state accuracy; report all-frame separately.
    core = np.ones(len(times), dtype=bool)
    for boundary in truth["boundaries"]:
        core &= abs(times - boundary) >= 0.08
    expected = np.isfinite(target) & core
    negative = ~np.isfinite(target) & core
    mutual = expected & np.isfinite(hz)
    signed = 12 * np.log2(hz[mutual] / target[mutual])
    errors = abs(signed)
    hz_error = abs(hz[mutual] - target[mutual])
    doubled = np.zeros(len(times), dtype=bool)
    halved = np.zeros(len(times), dtype=bool)
    doubled[mutual] = (signed >= 9) & (signed <= 15)
    halved[mutual] = (signed <= -9) & (signed >= -15)
    return {
        "known_voiced_frames": int(expected.sum()),
        "voiced_coverage": float(mutual.sum() / expected.sum()) if expected.any() else None,
        "false_gap_frames": int((expected & ~np.isfinite(hz)).sum()),
        "median_error_st": float(np.median(errors)) if len(errors) else None,
        "median_error_cents": float(100 * np.median(errors)) if len(errors) else None,
        "median_absolute_hz_error": float(np.median(hz_error)) if len(errors) else None,
        "p90_error_st": float(np.quantile(errors, 0.9)) if len(errors) else None,
        "p95_error_st": float(np.quantile(errors, 0.95)) if len(errors) else None,
        "p95_absolute_hz_error": float(np.quantile(hz_error, 0.95)) if len(errors) else None,
        "max_error_st": float(errors.max()) if len(errors) else None,
        "max_absolute_hz_error": float(hz_error.max()) if len(errors) else None,
        "octave_error_frames": int((errors > 9).sum()),
        "octave_doubling_frames": int(doubled.sum()),
        "octave_halving_frames": int(halved.sum()),
        "octave_doubling_events": len(runs(doubled)),
        "octave_halving_events": len(runs(halved)),
        "compared_frames": len(errors),
        "negative_frames": int(negative.sum()),
        "false_voiced_frames": int((negative & np.isfinite(hz)).sum()),
    }


def synthetic_signals(root: Path) -> list[dict[str, Any]]:
    """Ten harmonic controls plus digital silence, stationary noise and clicks."""
    rate = 16000
    t = np.arange(32000) / rate
    active = (t >= 0.2) & (t < 1.8)
    phase_time = np.clip((t - 0.2) / 1.6, 0, 1)
    contours = {
        **{f"steady_{v}": np.full(len(t), float(v)) for v in (70, 110, 180, 260)},
        "rise": 90 * 2 ** (1.7 * phase_time),
        "fall": 280 * 2 ** (-1.7 * phase_time),
        "valley": 120 + 55 * (2 * phase_time - 1) ** 2,
        "octave_risk": np.full(len(t), 110.0),
        "weak_fundamental": np.full(len(t), 110.0),
        "noise_gap": np.full(len(t), 110.0),
    }
    output = []
    rng = np.random.default_rng(20261005)
    for name, f0 in contours.items():
        phase = 2 * np.pi * np.cumsum(f0) / rate
        signal = np.zeros(len(t))
        for harmonic in range(1, 21):
            amp = 1 / harmonic**1.2
            if name == "weak_fundamental" and harmonic == 1:
                amp *= 0.03
            if name in {"weak_fundamental", "octave_risk"} and harmonic == 2:
                amp *= 5
            if name == "octave_risk" and harmonic % 2:
                amp *= 0.15 + 0.85 * (np.cos(2 * np.pi * phase_time) ** 2)
            signal += amp * np.sin(harmonic * phase + 0.13 * harmonic)
        envelope = np.minimum(np.clip((t - 0.2) / 0.025, 0, 1), np.clip((1.8 - t) / 0.025, 0, 1))
        signal = signal / max(abs(signal)) * 0.22 * envelope
        voiced = active.copy()
        boundaries = [0.2, 1.8]
        if name == "noise_gap":
            gap = (t >= 0.8) & (t < 1.1)
            voiced[gap] = False
            signal[gap] = rng.normal(0, 0.035, gap.sum())
            boundaries += [0.8, 1.1]
        hz = np.where(voiced, f0, np.nan)
        path = root / (name + ".wav")
        write_audio(path, signal, rate)
        truth = {
            "times": t[::160].tolist(),
            "f0_hz": [float(v) if np.isfinite(v) else None for v in hz[::160]],
            "boundaries": boundaries,
        }
        output.append(
            {
                "id": "syn_" + name,
                "audio_path": str(path),
                "kind": "synthetic",
                "truth": truth,
                "definition": name,
                "source_provenance": "deterministic local synthesis",
            }
        )
    for name in ("digital_silence", "stationary_noise", "clicks"):
        signal = np.zeros(len(t))
        if name == "stationary_noise":
            signal = rng.normal(0, 0.006, len(t))
        if name == "clicks":
            signal[8000] = 0.5
            signal[16000:16016] = 0.3 * np.hanning(16)
        path = root / (name + ".wav")
        write_audio(path, signal, rate)
        output.append(
            {
                "id": "neg_" + name,
                "audio_path": str(path),
                "kind": "negative",
                "source_provenance": "deterministic local synthesis",
            }
        )
    return output

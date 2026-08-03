"""Pitch analyzers and speaker-relative normalization.

The dependency-free autocorrelation analyzer is intentionally modest: it makes
the experiment runnable everywhere and provides a reference against optional
torchcrepe and Praat/Parselmouth. None of these analyzers assigns tone labels.
"""

from __future__ import annotations

import math
import statistics
import struct
import wave
from pathlib import Path
from typing import TYPE_CHECKING

from benchmark.models import (
    AcousticAnalysisResult,
    PitchPoint,
    TimeSpan,
    VoicedSegment,
)
from benchmark.providers.base import PitchAnalyzer

if TYPE_CHECKING:
    from collections.abc import Sequence


def _pcm16_mono(path: Path) -> tuple[int, list[float]]:
    with wave.open(str(path), "rb") as stream:
        if stream.getnchannels() != 1 or stream.getsampwidth() != 2:
            raise ValueError("pitch analyzers require mono PCM16 WAV")
        rate = stream.getframerate()
        raw = stream.readframes(stream.getnframes())
    count = len(raw) // 2
    samples = struct.unpack(f"<{count}h", raw)
    return rate, [sample / 32768.0 for sample in samples]


def normalize_pitch_points(points: Sequence[PitchPoint]) -> tuple[PitchPoint, ...]:
    voiced = [point.f0_hz for point in points if point.f0_hz is not None and point.f0_hz > 0]
    if not voiced:
        return tuple(points)
    log_values = [math.log(value) for value in voiced]
    median_hz = statistics.median(voiced)
    mean_log = statistics.fmean(log_values)
    std_log = statistics.pstdev(log_values)
    normalized: list[PitchPoint] = []
    for point in points:
        if point.f0_hz is None or point.f0_hz <= 0:
            normalized.append(point)
            continue
        semitones = 12.0 * math.log2(point.f0_hz / median_hz)
        z_log = (math.log(point.f0_hz) - mean_log) / std_log if std_log > 1e-9 else 0.0
        normalized.append(
            point.model_copy(update={"normalized_semitones": semitones, "z_log_f0": z_log})
        )
    return tuple(normalized)


def _segments(points: Sequence[PitchPoint], hop_seconds: float) -> tuple[VoicedSegment, ...]:
    result: list[VoicedSegment] = []
    current: list[PitchPoint] = []
    for point in [*points, PitchPoint(timestamp_seconds=10**12)]:
        if point.f0_hz is not None:
            current.append(point)
            continue
        if current:
            pitches = [item.f0_hz for item in current if item.f0_hz is not None]
            result.append(
                VoicedSegment(
                    span=TimeSpan(
                        start_seconds=current[0].timestamp_seconds,
                        end_seconds=current[-1].timestamp_seconds + hop_seconds,
                    ),
                    median_f0_hz=statistics.median(pitches),
                )
            )
            current = []
    return tuple(result)


def _features(points: Sequence[PitchPoint]) -> dict[str, float | None]:
    voiced = [point for point in points if point.normalized_semitones is not None]
    voiced_values = [
        point.normalized_semitones for point in points if point.normalized_semitones is not None
    ]
    if not points or not voiced or not voiced_values:
        return {
            "voiced_fraction": 0.0,
            "semitone_range": None,
            "start_end_slope_st_per_s": None,
        }
    values = voiced_values
    elapsed = voiced[-1].timestamp_seconds - voiced[0].timestamp_seconds
    slope = (values[-1] - values[0]) / elapsed if elapsed > 0 else 0.0
    return {
        "voiced_fraction": len(voiced) / len(points),
        "semitone_range": max(values) - min(values),
        "start_end_slope_st_per_s": slope,
    }


class AutocorrelationPitchAnalyzer(PitchAnalyzer):
    algorithm_name = "normalized_autocorrelation"
    algorithm_version = "1.0.0"

    def __init__(
        self,
        *,
        fmin_hz: float = 50.0,
        fmax_hz: float = 550.0,
        frame_seconds: float = 0.04,
        hop_seconds: float = 0.01,
        voicing_threshold: float = 0.32,
    ) -> None:
        self.fmin_hz = fmin_hz
        self.fmax_hz = fmax_hz
        self.frame_seconds = frame_seconds
        self.hop_seconds = hop_seconds
        self.voicing_threshold = voicing_threshold

    def analyze(self, audio_path: str) -> AcousticAnalysisResult:
        rate, samples = _pcm16_mono(Path(audio_path))
        frame_length = max(4, round(rate * self.frame_seconds))
        hop_length = max(1, round(rate * self.hop_seconds))
        min_lag = max(1, int(rate / self.fmax_hz))
        max_lag = min(frame_length - 2, int(rate / self.fmin_hz))
        points: list[PitchPoint] = []
        for offset in range(0, max(0, len(samples) - frame_length + 1), hop_length):
            frame = samples[offset : offset + frame_length]
            mean = statistics.fmean(frame)
            centered = [
                (value - mean) * (0.54 - 0.46 * math.cos(2 * math.pi * index / (frame_length - 1)))
                for index, value in enumerate(frame)
            ]
            energy = math.sqrt(statistics.fmean(value * value for value in centered))
            best_correlation = -1.0
            best_lag = min_lag
            for lag in range(min_lag, max_lag + 1):
                left = centered[:-lag]
                right = centered[lag:]
                numerator = sum(a * b for a, b in zip(left, right, strict=True))
                denominator = math.sqrt(sum(a * a for a in left) * sum(b * b for b in right))
                correlation = numerator / denominator if denominator > 1e-12 else 0.0
                if correlation > best_correlation:
                    best_correlation = correlation
                    best_lag = lag
            periodicity = min(1.0, max(0.0, best_correlation))
            voiced = energy >= 0.003 and periodicity >= self.voicing_threshold
            points.append(
                PitchPoint(
                    timestamp_seconds=(offset + frame_length / 2) / rate,
                    f0_hz=rate / best_lag if voiced else None,
                    voicing_probability=periodicity,
                    energy_rms=energy,
                )
            )
        normalized = normalize_pitch_points(points)
        return AcousticAnalysisResult(
            pitch_algorithm=self.algorithm_name,
            algorithm_version=self.algorithm_version,
            sample_rate_hz=rate,
            normalization_method="semitones_relative_to_utterance_median_and_z_log_f0",
            f0=normalized,
            voiced_segments=_segments(normalized, self.hop_seconds),
            contour_features=_features(normalized),
        )


class ParselmouthPitchAnalyzer(PitchAnalyzer):
    algorithm_name = "praat_autocorrelation_via_parselmouth"
    algorithm_version = "runtime"

    def analyze(self, audio_path: str) -> AcousticAnalysisResult:
        try:
            import parselmouth
        except ImportError as exc:
            raise RuntimeError("install the 'acoustics' extra for Parselmouth") from exc
        sound = parselmouth.Sound(audio_path)
        pitch = sound.to_pitch_ac(time_step=0.01, pitch_floor=50, pitch_ceiling=550)
        frequencies = pitch.selected_array["frequency"]
        points = [
            PitchPoint(
                timestamp_seconds=float(pitch.xs()[index]),
                f0_hz=float(value) if value > 0 else None,
                voicing_probability=None,
                energy_rms=None,
            )
            for index, value in enumerate(frequencies)
        ]
        normalized = normalize_pitch_points(points)
        return AcousticAnalysisResult(
            pitch_algorithm=self.algorithm_name,
            algorithm_version=(
                f"Parselmouth {parselmouth.VERSION}; Praat {parselmouth.PRAAT_VERSION}"
            ),
            sample_rate_hz=round(sound.sampling_frequency),
            normalization_method="semitones_relative_to_utterance_median_and_z_log_f0",
            f0=normalized,
            voiced_segments=_segments(normalized, 0.01),
            contour_features=_features(normalized),
        )


class TorchCrepePitchAnalyzer(PitchAnalyzer):
    algorithm_name = "torchcrepe_full_viterbi"
    algorithm_version = "runtime"

    def analyze(self, audio_path: str) -> AcousticAnalysisResult:
        try:
            import torch
            import torchcrepe
        except ImportError as exc:
            raise RuntimeError("install the 'acoustics' extra for torchcrepe") from exc
        rate, values = _pcm16_mono(Path(audio_path))
        audio = torch.tensor(values, dtype=torch.float32).unsqueeze(0)
        hop = round(rate * 0.01)
        pitch, periodicity = torchcrepe.predict(
            audio,
            rate,
            hop,
            50,
            550,
            "full",
            1024,
            "cpu",
            return_periodicity=True,
        )
        pitch = torchcrepe.threshold.At(0.21)(pitch, periodicity)
        points = []
        for index, (f0, confidence) in enumerate(zip(pitch[0], periodicity[0], strict=True)):
            value = float(f0)
            points.append(
                PitchPoint(
                    timestamp_seconds=index * hop / rate,
                    f0_hz=value if math.isfinite(value) and value > 0 else None,
                    voicing_probability=max(0.0, min(1.0, float(confidence))),
                )
            )
        normalized = normalize_pitch_points(points)
        return AcousticAnalysisResult(
            pitch_algorithm=self.algorithm_name,
            algorithm_version=getattr(torchcrepe, "__version__", "unknown"),
            sample_rate_hz=rate,
            normalization_method="semitones_relative_to_utterance_median_and_z_log_f0",
            f0=normalized,
            voiced_segments=_segments(normalized, hop / rate),
            contour_features=_features(normalized),
        )

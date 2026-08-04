"""Production acoustic evidence independent of benchmark domain models."""

from __future__ import annotations

import math
import statistics
import struct
import time
import uuid
import wave
from pathlib import Path
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from benma_api.db.models import AcousticRun, AudioAsset, Utterance
from benma_api.errors import AnalysisUnsupportedError, AuthorizationError, InvalidAudioError
from benma_api.storage.audio_store import AudioObjectStore


class AcousticAnalysisPort(Protocol):
    algorithm_name: str
    algorithm_version: str
    parameters: dict[str, Any]

    def analyze(self, path: Path) -> dict[str, Any]: ...


def _pcm16_mono(path: Path) -> tuple[int, list[float]]:
    try:
        with wave.open(str(path), "rb") as stream:
            if stream.getnchannels() != 1 or stream.getsampwidth() != 2:
                raise InvalidAudioError("acoustic analysis requires mono PCM16 WAV")
            rate = stream.getframerate()
            raw = stream.readframes(stream.getnframes())
    except (wave.Error, EOFError, OSError) as exc:
        raise InvalidAudioError("canonical audio is not readable PCM WAV") from exc
    count = len(raw) // 2
    if count == 0:
        raise InvalidAudioError("canonical audio has no samples")
    samples = struct.unpack(f"<{count}h", raw)
    return rate, [sample / 32768.0 for sample in samples]


def _downsample(points: list[dict[str, Any]], maximum: int = 240) -> list[dict[str, Any]]:
    """Min/max bucket sampling preserves contour extrema and explicit unvoiced gaps."""

    if len(points) <= maximum:
        return points
    bucket_size = math.ceil(len(points) / max(1, maximum // 3))
    selected: list[dict[str, Any]] = []
    for start in range(0, len(points), bucket_size):
        bucket = points[start : start + bucket_size]
        candidates = [bucket[0], bucket[-1]]
        voiced = [item for item in bucket if item["normalized_semitones"] is not None]
        if voiced:
            candidates.extend(
                (
                    min(voiced, key=lambda item: item["normalized_semitones"]),
                    max(voiced, key=lambda item: item["normalized_semitones"]),
                )
            )
        elif bucket:
            candidates.append(bucket[len(bucket) // 2])
        selected.extend(candidates)
    by_time = {item["timestamp_seconds"]: item for item in selected}
    return [by_time[key] for key in sorted(by_time)][:maximum]


class AutocorrelationAcousticAnalyzer:
    algorithm_name = "normalized_autocorrelation"
    algorithm_version = "2.0.0"

    def __init__(
        self,
        *,
        fmin_hz: float = 50.0,
        fmax_hz: float = 550.0,
        frame_seconds: float = 0.04,
        hop_seconds: float = 0.01,
        voicing_threshold: float = 0.32,
    ) -> None:
        self.parameters = {
            "fmin_hz": fmin_hz,
            "fmax_hz": fmax_hz,
            "frame_seconds": frame_seconds,
            "hop_seconds": hop_seconds,
            "voicing_threshold": voicing_threshold,
        }

    def analyze(self, path: Path) -> dict[str, Any]:
        rate, samples = _pcm16_mono(path)
        frame_length = max(4, round(rate * self.parameters["frame_seconds"]))
        hop_length = max(1, round(rate * self.parameters["hop_seconds"]))
        min_lag = max(1, int(rate / self.parameters["fmax_hz"]))
        max_lag = min(frame_length - 2, int(rate / self.parameters["fmin_hz"]))
        raw_points: list[dict[str, Any]] = []
        for offset in range(0, max(0, len(samples) - frame_length + 1), hop_length):
            frame = samples[offset : offset + frame_length]
            mean = statistics.fmean(frame)
            centered = [
                (value - mean)
                * (0.54 - 0.46 * math.cos(2 * math.pi * index / (frame_length - 1)))
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
            confidence = min(1.0, max(0.0, best_correlation))
            voiced = energy >= 0.003 and confidence >= self.parameters["voicing_threshold"]
            raw_points.append(
                {
                    "timestamp_seconds": round((offset + frame_length / 2) / rate, 4),
                    "f0_hz": round(rate / best_lag, 3) if voiced else None,
                    "voicing_probability": round(confidence, 4),
                    "energy_rms": round(energy, 6),
                }
            )
        voiced_hz = [item["f0_hz"] for item in raw_points if item["f0_hz"] is not None]
        median_hz = statistics.median(voiced_hz) if voiced_hz else None
        log_values = [math.log(value) for value in voiced_hz]
        mean_log = statistics.fmean(log_values) if log_values else None
        std_log = statistics.pstdev(log_values) if len(log_values) > 1 else 0.0
        points: list[dict[str, Any]] = []
        for point in raw_points:
            f0 = point["f0_hz"]
            normalized = (
                round(12 * math.log2(f0 / median_hz), 4)
                if f0 is not None and median_hz is not None
                else None
            )
            points.append(
                {
                    **point,
                    "normalized_semitones": normalized,
                    "z_log_f0": (
                        round((math.log(f0) - mean_log) / std_log, 4)
                        if f0 is not None
                        and mean_log is not None
                        and std_log is not None
                        and std_log > 1e-9
                        else (0.0 if f0 is not None else None)
                    ),
                }
            )
        normalized_values = [
            item["normalized_semitones"]
            for item in points
            if item["normalized_semitones"] is not None
        ]
        pitch_change = (
            normalized_values[-1] - normalized_values[0]
            if len(normalized_values) >= 2
            else None
        )
        rms = math.sqrt(statistics.fmean(value * value for value in samples))
        clipping_fraction = sum(abs(value) >= 0.98 for value in samples) / len(samples)
        voiced_fraction = len(voiced_hz) / len(points) if points else 0.0
        silence_fraction = (
            sum(float(point["energy_rms"]) < 0.003 for point in raw_points) / len(raw_points)
            if raw_points
            else 1.0
        )
        quality_issues: list[str] = []
        if rms < 0.005:
            quality_issues.append("too_quiet")
        if clipping_fraction > 0.02:
            quality_issues.append("clipping")
        if voiced_fraction < 0.15:
            quality_issues.append("low_voiced_fraction")
        if silence_fraction > 0.7:
            quality_issues.append("excessive_silence")
        return {
            "timestamps_unit": "seconds",
            "sample_rate_hz": rate,
            "duration_seconds": round(len(samples) / rate, 4),
            "f0": points,
            "mobile_f0": _downsample(points),
            "downsampling": {
                "method": "min_max_bucket_with_gap_preservation",
                "maximum_points": 240,
                "full_resolution_points": len(points),
            },
            "normalization": {
                "method": "semitones_relative_to_voiced_utterance_median_and_z_log_f0",
                "scope": "utterance_local",
                "baseline_hz": round(median_hz, 3) if median_hz is not None else None,
                "speaker_range_claim": "unavailable",
            },
            "contour_features": {
                "start_pitch_semitones": normalized_values[0] if normalized_values else None,
                "end_pitch_semitones": normalized_values[-1] if normalized_values else None,
                "change_semitones": round(pitch_change, 4) if pitch_change is not None else None,
                "minimum_semitones": min(normalized_values) if normalized_values else None,
                "maximum_semitones": max(normalized_values) if normalized_values else None,
                "range_semitones": (
                    round(max(normalized_values) - min(normalized_values), 4)
                    if normalized_values
                    else None
                ),
                "voiced_fraction": round(voiced_fraction, 4),
            },
            "recording_quality": {
                "status": "invalid_for_interpretation" if quality_issues else "usable",
                "issues": quality_issues,
                "rms": round(rms, 6),
                "clipping_fraction": round(clipping_fraction, 6),
                "silence_fraction": round(silence_fraction, 6),
            },
            "capability_state": "raw_evidence",
            "limitations": [
                "Autocorrelation can double or halve pitch and is not a Mandarin tone judge.",
                "Utterance-local normalization does not establish a speaker's pitch range.",
                "Low-confidence and unvoiced frames remain absent rather than interpolated.",
            ],
        }


class DisabledAcousticAnalyzer:
    algorithm_name = "disabled"
    algorithm_version = "1.0.0"
    def __init__(self) -> None:
        self.parameters: dict[str, Any] = {}

    def analyze(self, path: Path) -> dict[str, Any]:
        del path
        raise AnalysisUnsupportedError("acoustic analysis is disabled")


class AcousticAnalysisService:
    def __init__(
        self, db: Session, store: AudioObjectStore, analyzer: AcousticAnalysisPort
    ) -> None:
        self.db = db
        self.store = store
        self.analyzer = analyzer

    def run(
        self, *, account_id: uuid.UUID, utterance_id: uuid.UUID, reuse: bool = True
    ) -> AcousticRun:
        utterance = self.db.get(Utterance, utterance_id)
        if utterance is None or utterance.account_id != account_id:
            raise AuthorizationError("utterance was not found")
        if reuse:
            existing = self.db.scalar(
                select(AcousticRun)
                .where(
                    AcousticRun.account_id == account_id,
                    AcousticRun.utterance_id == utterance_id,
                    AcousticRun.algorithm == self.analyzer.algorithm_name,
                    AcousticRun.algorithm_version == self.analyzer.algorithm_version,
                    AcousticRun.status == "succeeded",
                )
                .order_by(AcousticRun.created_at.desc())
            )
            if existing is not None:
                return existing
        asset = self.db.get(AudioAsset, utterance.canonical_audio_asset_id)
        if asset is None or asset.account_id != account_id:
            raise AuthorizationError("canonical audio was not found")
        started = time.perf_counter()
        try:
            result = self.analyzer.analyze(self.store.path_for_processing(asset.storage_key))
            run = AcousticRun(
                account_id=account_id,
                utterance_id=utterance_id,
                algorithm=self.analyzer.algorithm_name,
                algorithm_version=self.analyzer.algorithm_version,
                parameters=self.analyzer.parameters,
                normalized_result=result,
                latency_ms=round((time.perf_counter() - started) * 1000),
                status="succeeded",
            )
            self.db.add(run)
            self.db.commit()
            return run
        except (AnalysisUnsupportedError, InvalidAudioError) as exc:
            run = AcousticRun(
                account_id=account_id,
                utterance_id=utterance_id,
                algorithm=self.analyzer.algorithm_name,
                algorithm_version=self.analyzer.algorithm_version,
                parameters=self.analyzer.parameters,
                latency_ms=round((time.perf_counter() - started) * 1000),
                status="failed",
                error_code=exc.code,
                error_message=exc.message,
            )
            self.db.add(run)
            self.db.commit()
            return run

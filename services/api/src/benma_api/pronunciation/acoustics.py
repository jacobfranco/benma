"""Production acoustic evidence independent of benchmark domain models."""

from __future__ import annotations

import math
import operator
import statistics
import struct
import time
import uuid
import wave
from collections.abc import Callable
from itertools import accumulate, pairwise
from pathlib import Path
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from benma_api.config import Settings
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
    bucket_size = math.ceil(len(points) / max(1, maximum // 5))
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
        unvoiced = [item for item in bucket if item["normalized_semitones"] is None]
        if unvoiced:
            candidates.append(unvoiced[0])
        selected.extend(candidates)
    by_time = {item["timestamp_seconds"]: item for item in selected}
    return [by_time[key] for key in sorted(by_time)][:maximum]


class AutocorrelationAcousticAnalyzer:
    algorithm_name = "normalized_autocorrelation"
    algorithm_version = "2.2.0"

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
        window = [
            0.54 - 0.46 * math.cos(2 * math.pi * index / (frame_length - 1))
            for index in range(frame_length)
        ]
        raw_points: list[dict[str, Any]] = []
        for offset in range(0, max(0, len(samples) - frame_length + 1), hop_length):
            frame = samples[offset : offset + frame_length]
            mean = statistics.fmean(frame)
            centered = [(value - mean) * window[index] for index, value in enumerate(frame)]
            energy = math.sqrt(statistics.fmean(value * value for value in centered))
            best_correlation = -1.0
            best_lag = min_lag
            # Prefix energies replace repeated Python sums at every lag. Same
            # normalized correlation; no resampling, new decoder, or F0 correction.
            energies = [0.0, *accumulate(value * value for value in centered)]
            for lag in range(min_lag, max_lag + 1):
                left = centered[:-lag]
                right = centered[lag:]
                numerator = sum(map(operator.mul, left, right))
                denominator = math.sqrt(
                    max(0.0, energies[frame_length - lag] * (energies[-1] - energies[lag]))
                )
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
        return acoustic_result(rate, samples, raw_points)


def acoustic_result(
    rate: int,
    samples: list[float],
    raw_points: list[dict[str, Any]],
) -> dict[str, Any]:
    """Common normalization/quality fields, without altering measurement-source samples."""
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
        item["normalized_semitones"] for item in points if item["normalized_semitones"] is not None
    ]
    pitch_change = (
        normalized_values[-1] - normalized_values[0] if len(normalized_values) >= 2 else None
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


def reject_terminal_octave_ambiguity(points: list[dict[str, Any]], threshold: float) -> None:
    """Exclude one short fading terminal octave branch; never manufacture a pitch.

    Requires measured energy decay, weak/missing alternate candidates, a coherent
    preceding region and a following loss of usable voicing. Interior changes,
    strong alternatives, sustained low pitch and repeated chaos are not repaired.
    Raw F0/candidates survive. The classifier still sees the unresolved raw jump.
    """
    voiced = [i for i, p in enumerate(points) if p.get("f0_hz")]
    jumps = [
        (a, b)
        for a, b in pairwise(voiced)
        if 0 < points[b]["timestamp_seconds"] - points[a]["timestamp_seconds"] <= 0.03
        and abs(12 * math.log2(points[b]["f0_hz"] / points[a]["f0_hz"])) > 6
    ]
    if len(jumps) != 1:
        return
    a, b = jumps[0]
    before, first = points[a], points[b]
    jump = 12 * math.log2(first["f0_hz"] / before["f0_hz"])
    if not -13 <= jump <= -11 or not before.get("quality_usable", True):
        return
    preceding = points[max(0, a - 4) : a + 1]
    if len(preceding) < 5 or any(
        not p.get("f0_hz") or not p.get("quality_usable") for p in preceding
    ):
        return
    tail = []
    for point in points[b:]:
        if not point.get("f0_hz") or not point.get("quality_usable", True):
            break
        tail.append(point)
    if not tail or tail[-1]["timestamp_seconds"] - first["timestamp_seconds"] > 0.08:
        return
    if first["energy_rms"] > before["energy_rms"] * 0.8 or tail[-1]["energy_rms"] > threshold * 1.2:
        return
    for point in tail:
        if abs(12 * math.log2(point["f0_hz"] / first["f0_hz"])) > 1.5:
            return
        candidates = point.get("pitch_candidates")
        if candidates is None:
            return
        if any(
            c["frequency_hz"] > 0
            and abs(12 * math.log2(c["frequency_hz"] / (2 * point["f0_hz"]))) < 1
            and c["strength"] >= 0.45
            for c in candidates
        ):
            return
    # A later speech region would make this an interior event, not a terminal tail.
    if any(p.get("f0_hz") and p.get("quality_usable") for p in points[b + len(tail) :]):
        return
    for point in tail:
        point["low_frequency_contaminated"] = False
        point["quality_usable"] = False
        point["selected_f0_hz"] = None
        point["selection_reason"] = "terminal_octave_ambiguity_no_supported_alternative"


class PraatAcousticAnalyzer:
    algorithm_name = "praat_autocorrelation"

    def __init__(self) -> None:
        import parselmouth

        self.algorithm_version = (
            f"1.2.0-parselmouth-{parselmouth.VERSION}-praat-{parselmouth.PRAAT_VERSION}"
        )
        self.parameters: dict[str, Any] = {
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
            "energy_gate": "bounded-recording-noise-floor-v1",
            "quality_gate": "spectral-and-filter-disagreement-v1",
        }

    def analyze(self, path: Path) -> dict[str, Any]:
        import numpy as np
        import parselmouth
        from parselmouth.praat import call

        rate, samples = _pcm16_mono(path)
        sound = parselmouth.Sound(str(path))
        values = sound.values[0]
        width, hop = round(rate * 0.04), round(rate * 0.01)
        energies = [
            float(np.sqrt(np.mean(values[i : i + width] ** 2)))
            for i in range(0, max(1, len(values) - width + 1), hop)
        ]
        # Gate periodic background energy without assigning it a pitch. Capped
        # relative to peak RMS so continuous quiet speech is not its own noise floor.
        floor = float(np.quantile(energies, 0.1))
        threshold = max(0.003, min(3 * floor, max(energies) * 0.15))
        points: list[dict[str, Any]] = []
        if len(samples) / rate >= 0.06:
            pitch_parameters = {
                k: v for k, v in self.parameters.items() if k not in {"energy_gate", "quality_gate"}
            }
            pitch = sound.to_pitch_ac(**pitch_parameters)
            # A second track detects susceptibility to low-frequency contamination.
            # It NEVER replaces the measured F0 or repairs an octave choice.
            filtered = call(sound, "Filter (pass Hann band)", 70, 0, 20)
            comparison = filtered.to_pitch_ac(**pitch_parameters)
            for frame_index, (timestamp, hz, strength, check_hz) in enumerate(
                zip(
                    pitch.xs(),
                    pitch.selected_array["frequency"],
                    pitch.selected_array["strength"],
                    comparison.selected_array["frequency"],
                    strict=True,
                )
            ):
                center = round(float(timestamp) * rate)
                frame = values[max(0, center - width // 2) : center + width // 2]
                rms = float(np.sqrt(np.mean(frame**2)))
                spectral_width = round(rate * 0.1)
                spectral = values[
                    max(0, center - spectral_width // 2) : center + spectral_width // 2
                ]
                power = (
                    np.abs(np.fft.rfft((spectral - spectral.mean()) * np.hanning(len(spectral))))
                    ** 2
                )
                frequencies = np.fft.rfftfreq(len(spectral), 1 / rate)
                low_fraction = float(
                    power[(frequencies >= 40) & (frequencies <= 80)].sum()
                    / max(1e-12, power[(frequencies >= 40) & (frequencies <= 4000)].sum())
                )
                disagreement = abs(12 * math.log2(hz / check_hz)) if hz > 0 and check_hz > 0 else 0
                contaminated = bool(
                    hz > 0 and ((hz < 80 and low_fraction > 0.7) or disagreement > 6)
                )
                points.append(
                    {
                        "timestamp_seconds": round(float(timestamp), 4),
                        "f0_hz": round(float(hz), 3) if hz > 0 and rms >= threshold else None,
                        "tracker_f0_hz": round(float(hz), 3) if hz > 0 else None,
                        "voicing_probability": round(min(1.0, max(0.0, float(strength))), 4),
                        "energy_rms": round(rms, 6),
                        "energy_gated": bool(hz > 0 and rms < threshold),
                        "low_frequency_energy_fraction": round(low_fraction, 4),
                        "comparison_f0_hz": round(float(check_hz), 3) if check_hz > 0 else None,
                        "filter_disagreement_st": round(disagreement, 3),
                        "quality_usable": not contaminated,
                        "low_frequency_contaminated": contaminated,
                        "selected_f0_hz": round(float(hz), 3)
                        if hz > 0 and rms >= threshold and not contaminated
                        else None,
                        "selection_reason": "low_frequency_contamination"
                        if contaminated
                        else "below_energy_gate"
                        if rms < threshold
                        else "praat_selected",
                        "pitch_candidates": [
                            {
                                "frequency_hz": round(float(c.frequency), 3),
                                "strength": round(float(c.strength), 4),
                            }
                            for c in pitch[frame_index].candidates
                            if 0 < c.frequency <= self.parameters["pitch_ceiling"]
                        ],
                    }
                )
        reject_terminal_octave_ambiguity(points, threshold)
        result = acoustic_result(rate, samples, points)
        result["channel_count"] = 1
        result["selection"] = {
            "version": "bounded-terminal-ambiguity-v1",
            "repaired_frame_count": 0,
            "artifact_rejected_frame_count": sum(
                p["selection_reason"] == "terminal_octave_ambiguity_no_supported_alternative"
                for p in points
            ),
            "policy": "reject_unsupported_terminal_branch_never_unwrap",
        }
        result["energy_gate"] = {"threshold_rms": threshold, "noise_floor_rms": floor}
        result["limitations"] = [
            "Praat reduces but cannot eliminate octave errors or creaky-voice ambiguity.",
            "The original tracker frequency remains stored alongside the energy-gated F0.",
            "Filtered-track disagreement flags ambiguous evidence; it never substitutes a pitch.",
            "Utterance-relative pitch is not a lexical-tone or intended-target correctness score.",
        ]
        return result


def build_acoustic_analyzer(settings: Settings) -> AcousticAnalysisPort:
    if settings.acoustic_provider == "praat":
        return PraatAcousticAnalyzer()
    if settings.acoustic_provider == "autocorrelation":
        return AutocorrelationAcousticAnalyzer()
    return DisabledAcousticAnalyzer()


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
        run = self.prepare(account_id=account_id, utterance_id=utterance_id, reuse=reuse)()
        self.db.add(run)
        self.db.commit()
        return run

    def prepare(
        self, *, account_id: uuid.UUID, utterance_id: uuid.UUID, reuse: bool = True
    ) -> Callable[[], AcousticRun]:
        # Every entry point, including prepared laboratory work, must hold this
        # lock until persistence. NO KEY UPDATE permits concurrent perception FKs.
        utterance = self.db.scalar(
            select(Utterance)
            .where(Utterance.id == utterance_id, Utterance.account_id == account_id)
            .with_for_update(key_share=True)
        )
        if utterance is None or utterance.account_id != account_id:
            raise AuthorizationError("utterance was not found")
        if reuse:
            candidates = self.db.scalars(
                select(AcousticRun)
                .where(
                    AcousticRun.account_id == account_id,
                    AcousticRun.utterance_id == utterance_id,
                    AcousticRun.algorithm == self.analyzer.algorithm_name,
                    AcousticRun.algorithm_version == self.analyzer.algorithm_version,
                )
                .order_by(AcousticRun.created_at.desc())
            )
            for existing in candidates:
                if existing.parameters == self.analyzer.parameters:
                    return lambda: existing
        asset = self.db.get(AudioAsset, utterance.canonical_audio_asset_id)
        if asset is None or asset.account_id != account_id:
            raise AuthorizationError("canonical audio was not found")
        audio_path = self.store.path_for_processing(asset.storage_key)

        analyzer = self.analyzer
        audio_sha256 = asset.sha256
        audio_duration = asset.duration_seconds

        def compute() -> AcousticRun:
            started = time.perf_counter()
            try:
                result = analyzer.analyze(audio_path)
                if "duration_seconds" not in result and audio_duration is not None:
                    result = {**result, "duration_seconds": audio_duration}
                from benma_api.pronunciation.pitch_evidence import build_pitch_track

                track = build_pitch_track(
                    result,
                    audio_sha256=audio_sha256,
                    tracker_source=analyzer.algorithm_name,
                    tracker_version=analyzer.algorithm_version,
                    parameters=analyzer.parameters,
                )
                result = {**result, "utterance_pitch_track": track.model_dump(mode="json")}
                run = AcousticRun(
                    account_id=account_id,
                    utterance_id=utterance_id,
                    algorithm=analyzer.algorithm_name,
                    algorithm_version=analyzer.algorithm_version,
                    parameters=analyzer.parameters,
                    normalized_result=result,
                    latency_ms=round((time.perf_counter() - started) * 1000),
                    status="succeeded",
                )
                return run
            except Exception as caught:
                exc = (
                    caught
                    if isinstance(caught, (AnalysisUnsupportedError, InvalidAudioError))
                    else AnalysisUnsupportedError("Analysis unavailable")
                )
                run = AcousticRun(
                    account_id=account_id,
                    utterance_id=utterance_id,
                    algorithm=analyzer.algorithm_name,
                    algorithm_version=analyzer.algorithm_version,
                    parameters=analyzer.parameters,
                    latency_ms=round((time.perf_counter() - started) * 1000),
                    status="failed",
                    error_code=exc.code,
                    error_message=exc.message,
                )
                return run

        return compute

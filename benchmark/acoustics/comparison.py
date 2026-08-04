"""Side-by-side pitch algorithm comparison with explicit evidence provenance."""

from __future__ import annotations

import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from benchmark.acoustics.pitch import (
    AutocorrelationPitchAnalyzer,
    ParselmouthPitchAnalyzer,
    TorchCrepePitchAnalyzer,
)
from benchmark.models import AcousticAnalysisResult
from benchmark.providers.base import PitchAnalyzer
from benchmark.storage import write_json, write_model


def _summary(result: AcousticAnalysisResult) -> dict[str, Any]:
    voiced = [point for point in result.f0 if point.f0_hz is not None]
    return {
        "algorithm": result.pitch_algorithm,
        "algorithm_version": result.algorithm_version,
        "point_count": len(result.f0),
        "voiced_point_count": len(voiced),
        "voiced_fraction": len(voiced) / len(result.f0) if result.f0 else None,
        "contour_features": result.contour_features,
    }


def _pairwise(left: AcousticAnalysisResult, right: AcousticAnalysisResult) -> dict[str, Any]:
    right_by_time = {round(point.timestamp_seconds, 3): point for point in right.f0}
    differences: list[float] = []
    compared = 0
    voicing_agreements = 0
    for point in left.f0:
        other = right_by_time.get(round(point.timestamp_seconds, 3))
        if other is None:
            continue
        compared += 1
        if (point.f0_hz is None) == (other.f0_hz is None):
            voicing_agreements += 1
        if point.normalized_semitones is not None and other.normalized_semitones is not None:
            differences.append(abs(point.normalized_semitones - other.normalized_semitones))
    return {
        "left": left.pitch_algorithm,
        "right": right.pitch_algorithm,
        "matched_timestamp_count": compared,
        "voicing_agreement_fraction": voicing_agreements / compared if compared else None,
        "median_absolute_semitone_difference": (
            statistics.median(differences) if differences else None
        ),
        "shared_voiced_count": len(differences),
    }


def compare_pitch_algorithms(
    audio_paths: list[Path], *, output_dir: Path, evidence_origin: str
) -> dict[str, Any]:
    analyzers: tuple[PitchAnalyzer, ...] = (
        AutocorrelationPitchAnalyzer(),
        ParselmouthPitchAnalyzer(),
        TorchCrepePitchAnalyzer(),
    )
    results_by_audio: dict[str, list[AcousticAnalysisResult]] = defaultdict(list)
    failures: list[dict[str, str]] = []
    for audio_path in audio_paths:
        for analyzer in analyzers:
            try:
                result = analyzer.analyze(str(audio_path))
            except RuntimeError as exc:
                failures.append(
                    {
                        "audio": str(audio_path),
                        "algorithm": analyzer.algorithm_name,
                        "error": str(exc),
                    }
                )
                continue
            results_by_audio[str(audio_path)].append(result)
            write_model(
                output_dir / audio_path.stem / f"{result.pitch_algorithm}.json",
                result,
            )
    audio_rows: list[dict[str, Any]] = []
    for audio_key, results in results_by_audio.items():
        comparisons = [
            _pairwise(left, right)
            for left_index, left in enumerate(results)
            for right in results[left_index + 1 :]
        ]
        audio_rows.append(
            {
                "audio": audio_key,
                "algorithms": [_summary(result) for result in results],
                "pairwise": comparisons,
            }
        )
    real = evidence_origin == "real_recording"
    report = {
        "evidence_origin": evidence_origin,
        "audio_count": len(audio_paths),
        "real_audio_count": len(audio_paths) if real else 0,
        "results": audio_rows,
        "failures": failures,
        "production_decision": "keep_autocorrelation",
        "decision_reason": (
            "No reviewed real-recording comparison is available; preserve the current "
            "dependency-light analyzer."
            if not real or not audio_rows
            else (
                "Comparison evidence is available but requires manual contour review "
                "before change."
            )
        ),
        "automatic_algorithm_promotion": False,
    }
    write_json(output_dir / "acoustic-comparison.json", report)
    return report

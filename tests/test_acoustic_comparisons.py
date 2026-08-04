from __future__ import annotations

from pathlib import Path

from benchmark.acoustics.alignment_comparison import compare_alignment_files
from benchmark.acoustics.comparison import compare_pitch_algorithms
from benchmark.models import AlignmentResult, AlignmentUnit, TimeSpan
from benchmark.storage import write_model


def _alignment(offset: float) -> AlignmentResult:
    return AlignmentResult(
        algorithm="fixture",
        algorithm_version="1",
        words=(
            AlignmentUnit(label="ni3", span=TimeSpan(start_seconds=0, end_seconds=0.4)),
            AlignmentUnit(
                label="hao3",
                span=TimeSpan(start_seconds=0.4 + offset, end_seconds=0.8 + offset),
            ),
        ),
    )


def test_alignment_comparison_is_labeled_and_non_promoting(tmp_path: Path) -> None:
    manual = tmp_path / "manual.json"
    candidate = tmp_path / "candidate.json"
    write_model(manual, _alignment(0))
    write_model(candidate, _alignment(0.05))
    report = compare_alignment_files(
        manual,
        {"mfa": candidate},
        output_path=tmp_path / "comparison.json",
        evidence_origin="synthetic_test",
    )
    assert report["candidates"]["mfa"]["mean_absolute_boundary_error_seconds"] > 0
    assert report["automatic_alignment_promotion"] is False
    assert report["evidence_origin"] == "synthetic_test"


def test_pitch_comparison_keeps_production_algorithm_without_real_evidence(
    tmp_path: Path, canonical_wav: Path
) -> None:
    report = compare_pitch_algorithms(
        [canonical_wav], output_dir=tmp_path / "out", evidence_origin="synthetic_test"
    )
    assert report["audio_count"] == 1
    assert report["real_audio_count"] == 0
    assert report["production_decision"] == "keep_autocorrelation"
    assert report["automatic_algorithm_promotion"] is False

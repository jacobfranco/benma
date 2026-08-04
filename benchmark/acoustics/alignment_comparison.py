"""Compare provider/MFA boundaries against explicit manual reference intervals."""

from __future__ import annotations

import statistics
from pathlib import Path
from typing import Any

from benchmark.models import AlignmentResult, AlignmentUnit
from benchmark.storage import load_model, write_json


def compare_alignment(
    reference: tuple[AlignmentUnit, ...], candidate: tuple[AlignmentUnit, ...]
) -> dict[str, Any]:
    matched = min(len(reference), len(candidate))
    start_errors = [
        abs(reference[index].span.start_seconds - candidate[index].span.start_seconds)
        for index in range(matched)
    ]
    end_errors = [
        abs(reference[index].span.end_seconds - candidate[index].span.end_seconds)
        for index in range(matched)
    ]
    all_errors = [*start_errors, *end_errors]
    return {
        "reference_unit_count": len(reference),
        "candidate_unit_count": len(candidate),
        "matched_unit_count": matched,
        "label_match_count": sum(
            reference[index].label == candidate[index].label for index in range(matched)
        ),
        "mean_absolute_boundary_error_seconds": (
            statistics.fmean(all_errors) if all_errors else None
        ),
        "max_absolute_boundary_error_seconds": max(all_errors) if all_errors else None,
        "count_mismatch": len(reference) != len(candidate),
    }


def compare_alignment_files(
    manual_path: Path,
    candidates: dict[str, Path],
    *,
    output_path: Path,
    evidence_origin: str,
) -> dict[str, Any]:
    manual = load_model(manual_path, AlignmentResult)
    rows = {
        name: compare_alignment(manual.words or manual.phones, result.words or result.phones)
        for name, path in candidates.items()
        if (result := load_model(path, AlignmentResult))
    }
    report = {
        "evidence_origin": evidence_origin,
        "manual_reference": str(manual_path),
        "candidates": rows,
        "production_decision": "retain_provenance_separated_provider_and_mfa_timings",
        "automatic_alignment_promotion": False,
        "decision_reason": (
            "No reviewed real manual-boundary comparison is available."
            if evidence_origin != "real_recording"
            else "Manual comparison is available; inspect failures before changing production."
        ),
    }
    write_json(output_path, report)
    return report

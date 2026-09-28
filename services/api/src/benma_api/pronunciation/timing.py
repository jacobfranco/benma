"""Resolve persisted target timing without changing provider evidence or inventing spans."""

from __future__ import annotations

import math
from typing import Any

from benma_api.pronunciation.alignment import syllable_labels_match, validate_alignment


def resolve_target_timing(
    evidence: dict[str, Any],
    *,
    status: str,
    characters: list[str],
    readings: list[str],
    acoustic: dict[str, Any],
) -> dict[str, Any]:
    """A whole-recording coverage failure may be recording padding, not missing speech.

    Only that failure can be reconsidered, with independent energy AND periodic
    evidence concentrated inside the unchanged provider spans. All structural,
    identity and synthetic-evidence gates remain mandatory. Missing acoustic
    metadata fails closed. This pure derivation works for old rows and warmups.
    """
    units = evidence.get("units", [])
    if not isinstance(units, list) or any(not isinstance(u, dict) for u in units):
        return {"accepted": False, "reason": "invalid_timing_units", "sources": []}
    result: dict[str, Any] = {
        "accepted": False,
        "reason": "timing_unavailable",
        "persisted_quality": evidence.get("quality"),
        "sources": sorted({str(u.get("source")) for u in units if u.get("source")}),
    }
    if status != "succeeded":
        return result
    if evidence.get("evidence_status") not in {"live_provider", "live_tool"}:
        return {**result, "reason": "unverified_timing_provenance"}
    if not syllable_labels_match(units, characters, readings):
        return {**result, "reason": "target_unit_identity_mismatch"}
    duration = acoustic.get("duration_seconds")
    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        return {**result, "reason": "audio_duration_unavailable"}
    try:
        quality = validate_alignment(units, target_count=len(characters), duration_seconds=duration)
    except (KeyError, TypeError, ValueError, OverflowError):
        return {**result, "reason": "invalid_timing_fields"}
    issues = quality["issues"]
    # Never override another persisted rejection, including unknown future checks.
    persisted = evidence.get("quality") or {}
    persisted_issues = persisted.get("issues", [])
    if any(issue != "excessive_unaligned_audio" for issue in persisted_issues):
        return {**result, "reason": "persisted_timing_rejected", "issues": persisted_issues}
    if not issues and persisted.get("usable_for_syllable_visualization"):
        return {**result, "accepted": True, "reason": "validated_provider_span"}
    if issues != ["excessive_unaligned_audio"]:
        return {**result, "reason": "invalid_alignment", "issues": issues}
    raw = acoustic.get("f0", [])
    gate = acoustic.get("energy_gate", {}).get("threshold_rms")
    if not raw or not isinstance(gate, (int, float)) or not math.isfinite(gate) or gate <= 0:
        return {**result, "reason": "padding_evidence_unavailable"}
    threshold = max(gate, max(p.get("energy_rms", 0) for p in raw) * 0.2)
    active = [p for p in raw if p.get("energy_rms", 0) >= threshold]
    voiced = [
        p
        for p in raw
        if p.get("f0_hz")
        and p.get("quality_usable", True)
        and p.get("voicing_probability", 0) >= 0.45
    ]

    def covered(point: dict[str, Any]) -> bool:
        # Frame windows straddle provider boundaries; this never changes slicing bounds.
        return any(
            u["start_seconds"] - 0.06 <= point["timestamp_seconds"] <= u["end_seconds"] + 0.06
            for u in units
        )

    active_coverage = sum(map(covered, active)) / len(active) if active else 0.0
    voiced_coverage = sum(map(covered, voiced)) / len(voiced) if voiced else 0.0
    accepted = (
        len(active) >= 10 and len(voiced) >= 10 and min(active_coverage, voiced_coverage) >= 0.95
    )
    return {
        **result,
        "accepted": accepted,
        "reason": "acoustically_supported_recording_padding" if accepted else "unaligned_activity",
        "active_frame_coverage": round(active_coverage, 4),
        "voiced_frame_coverage": round(voiced_coverage, 4),
        "active_frame_count": len(active),
        "voiced_frame_count": len(voiced),
        "activity_threshold_rms": threshold,
    }

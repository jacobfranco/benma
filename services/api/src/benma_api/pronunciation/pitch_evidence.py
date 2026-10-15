"""Audio-only snapshots, exact projections, and conservative completeness checks.

No estimator, repair, linguistic identity, or reference contour is introduced here.
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from itertools import pairwise
from typing import Any

from benma_api.pronunciation.pitch_types import (
    TRACK_VERSION,
    PitchCandidate,
    PitchInterpretationEligibility,
    PitchRegionProjection,
    PitchSupportMetrics,
    UtterancePitchFrame,
    UtterancePitchTrack,
)
from benma_api.schemas import DisplayContour, DisplayPitchPoint, ObservedContour


def build_pitch_track(
    result: dict[str, Any],
    *,
    audio_sha256: str,
    tracker_source: str,
    tracker_version: str,
    parameters: dict[str, Any],
) -> UtterancePitchTrack:
    from benma_api.pronunciation.contours import DISPLAY_VERSION, display_contour

    raw = result.get("f0", [])
    diagnostics: list[dict[str, Any]] = []
    display = display_contour(raw, diagnostics=diagnostics)
    selected = {p.timestamp_seconds: p for s in display.segments for p in s}
    native = all("tracker_f0_hz" in p for p in raw)
    frames = tuple(
        UtterancePitchFrame(
            timestamp_seconds=p["timestamp_seconds"],
            raw_f0_hz=p.get("tracker_f0_hz") if native else p.get("f0_hz"),
            energy_gated_f0_hz=p.get("f0_hz"),
            analyzer_selected_f0_hz=p.get("selected_f0_hz"),
            selected_f0_hz=p.get("f0_hz") if d["retained"] else None,
            periodicity=p.get("voicing_probability"),
            energy_rms=p.get("energy_rms"),
            comparison_f0_hz=p.get("comparison_f0_hz"),
            filter_disagreement_st=p.get("filter_disagreement_st"),
            candidates=tuple(
                PitchCandidate.model_validate(c) for c in p.get("pitch_candidates", [])
            ),
            exclusion_reasons=tuple(d["reasons"]),
            display_semitones=selected[p["timestamp_seconds"]].normalized_semitones
            if d["retained"]
            else None,
        )
        for p, d in zip(raw, diagnostics, strict=True)
    )
    cadence = (
        statistics.median(b.timestamp_seconds - a.timestamp_seconds for a, b in pairwise(frames))
        if len(frames) > 1
        else None
    )
    # Include the measurements themselves, not just configuration: changed evidence
    # can never accidentally keep an old identifier. Timing/text is absent by type.
    payload = dict(
        schema_version=TRACK_VERSION,
        audio_sha256=audio_sha256,
        tracker_source=tracker_source,
        tracker_version=tracker_version,
        tracker_configuration_json=json.dumps(parameters, sort_keys=True, separators=(",", ":")),
        selection_version=DISPLAY_VERSION,
        raw_provenance="native_tracker" if native else "legacy_energy_gated",
        frame_cadence_seconds=round(cadence, 8) if cadence else None,
        duration_seconds=result.get(
            "duration_seconds", frames[-1].timestamp_seconds if frames else 0
        ),
        baseline_hz=display.baseline_hz,
        frames=[f.model_dump(mode="json") for f in frames],
    )
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return UtterancePitchTrack.model_validate({**payload, "evidence_id": digest})


def load_pitch_track(
    result: dict[str, Any],
    *,
    audio_sha256: str,
    tracker_source: str,
    tracker_version: str,
    parameters: dict[str, Any],
) -> UtterancePitchTrack:
    """Replay saved selection; wrap legacy raw JSON without changing its history."""
    if saved := result.get("utterance_pitch_track"):
        track = UtterancePitchTrack.model_validate(saved)
        if track.audio_sha256 != audio_sha256:
            raise ValueError("pitch evidence does not belong to this audio")
        return track
    return build_pitch_track(
        result,
        audio_sha256=audio_sha256,
        tracker_source=tracker_source,
        tracker_version=tracker_version,
        parameters=parameters,
    )


def display_from_track(track: UtterancePitchTrack) -> DisplayContour:
    segments: list[list[DisplayPitchPoint]] = []
    current: list[DisplayPitchPoint] = []
    for frame in track.frames:
        if frame.display_semitones is None:
            if current:
                segments.append(current)
                current = []
            continue
        if current and frame.timestamp_seconds - current[-1].timestamp_seconds > 0.045:
            segments.append(current)
            current = []
        current.append(
            DisplayPitchPoint(
                timestamp_seconds=frame.timestamp_seconds,
                normalized_semitones=frame.display_semitones,
            )
        )
    if current:
        segments.append(current)
    heights = [p.normalized_semitones for s in segments for p in s]
    return DisplayContour(
        segments=segments,
        baseline_hz=track.baseline_hz,
        minimum_semitones=min(-3, min(heights, default=0) - 1),
        maximum_semitones=max(3, max(heights, default=0) + 1),
        rejected_points=sum(
            f.energy_gated_f0_hz is not None and f.selected_f0_hz is None for f in track.frames
        ),
        method=track.selection_version,
    )


def project_pitch(
    track: UtterancePitchTrack,
    start: float | None,
    end: float | None,
    *,
    timing_source: str | None,
    timing_evidence_id: str | None = None,
) -> PitchRegionProjection:
    if (
        start is None
        or end is None
        or not math.isfinite(start)
        or not math.isfinite(end)
        or not 0 <= start < end <= track.duration_seconds + 0.0001
        or not timing_source
        or timing_source in {"synthetic", "synthetic_replay", "equal_split"}
    ):
        return PitchRegionProjection(track_evidence_id=track.evidence_id)
    return PitchRegionProjection(
        track_evidence_id=track.evidence_id,
        start_seconds=start,
        end_seconds=end,
        timing_source=timing_source,
        timing_evidence_id=timing_evidence_id,
        frame_indices=tuple(
            i for i, f in enumerate(track.frames) if start <= f.timestamp_seconds < end
        ),
    )


def interpretation_eligibility(
    track: UtterancePitchTrack,
    region: PitchRegionProjection,
    *,
    _interpretation_raw: list[UtterancePitchFrame] | None = None,
) -> PitchInterpretationEligibility:
    if region.track_evidence_id != track.evidence_id:
        raise ValueError("projection belongs to a different pitch track")
    if region.start_seconds is None:
        return PitchInterpretationEligibility()
    frames = [track.frames[i] for i in region.frame_indices]
    raw = (
        [f for f in frames if f.raw_f0_hz is not None]
        if _interpretation_raw is None
        else _interpretation_raw
    )
    selected = [f for f in raw if f.selected_f0_hz is not None]
    hop = track.frame_cadence_seconds or 0.01
    if not raw:
        return PitchInterpretationEligibility(reasons=("no_voiced_support",))
    extent = raw[-1].timestamp_seconds - raw[0].timestamp_seconds + hop
    thirds = [
        [
            f
            for f in raw
            if min(2, int(3 * (f.timestamp_seconds - raw[0].timestamp_seconds) / extent)) == k
        ]
        for k in range(3)
    ]
    retention = [
        sum(f.selected_f0_hz is not None for f in third) / len(third) if third else 0
        for third in thirds
    ]
    runs: list[list[UtterancePitchFrame]] = []
    current: list[UtterancePitchFrame] = []
    for f in frames:
        if current and (
            f.selected_f0_hz is None
            or f.timestamp_seconds - current[-1].timestamp_seconds > 1.5 * hop
        ):
            runs.append(current)
            current = []
        if f.selected_f0_hz is not None:
            current.append(f)
    if current:
        runs.append(current)
    jumps = [
        abs(12 * math.log2(b.raw_f0_hz / a.raw_f0_hz))
        for a, b in pairwise(raw)
        if a.raw_f0_hz and b.raw_f0_hz and b.timestamp_seconds - a.timestamp_seconds <= 0.12
    ]
    m = PitchSupportMetrics(
        raw_voiced_frames=len(raw),
        selected_frames=len(selected),
        raw_start_seconds=raw[0].timestamp_seconds,
        raw_end_seconds=raw[-1].timestamp_seconds,
        selected_start_seconds=selected[0].timestamp_seconds if selected else None,
        selected_end_seconds=selected[-1].timestamp_seconds if selected else None,
        retained_fraction=len(selected) / len(raw),
        early_retained_fraction=retention[0],
        middle_retained_fraction=retention[1],
        late_retained_fraction=retention[2],
        largest_island_seconds=max(
            (r[-1].timestamp_seconds - r[0].timestamp_seconds + hop for r in runs), default=0
        ),
        selected_islands=len(runs),
        largest_raw_gap_seconds=max(
            (b.timestamp_seconds - a.timestamp_seconds - hop for a, b in pairwise(raw)), default=0
        ),
        largest_selected_gap_seconds=max(
            (b.timestamp_seconds - a.timestamp_seconds - hop for a, b in pairwise(selected)),
            default=0,
        ),
        missing_head_seconds=selected[0].timestamp_seconds - raw[0].timestamp_seconds
        if selected
        else extent,
        missing_tail_seconds=raw[-1].timestamp_seconds - selected[-1].timestamp_seconds
        if selected
        else extent,
        maximum_raw_jump_semitones=max(jumps, default=0),
        discontinuities=sum(j > 6 for j in jumps),
    )
    reasons: list[str] = []
    # Never require F0 in unvoiced margins; loss is measured against RAW voicing.
    if max(m.missing_head_seconds, m.missing_tail_seconds) >= max(0.05, extent * 0.2):
        reasons.append("voiced_boundary_lost")
    if m.retained_fraction < 0.7 or min(retention) < 0.5:
        reasons.append("raw_to_selected_attrition")
    if m.discontinuities:
        reasons.append("raw_pitch_discontinuity")
    if m.largest_raw_gap_seconds > 0.08 or m.largest_selected_gap_seconds > 0.08:
        reasons.append("fragmented_voiced_support")
    if len(selected) < 12 or m.largest_island_seconds < 0.12 - 1e-8:
        state = "insufficient"
        reasons.insert(0, "too_little_sustained_evidence")
    elif "voiced_boundary_lost" in reasons or "raw_to_selected_attrition" in reasons:
        state = "incomplete"
    elif reasons:
        state = "unstable"
    elif track.raw_provenance != "native_tracker":
        state = "insufficient"
        reasons.append("raw_tracker_history_unavailable")
    else:
        state = "sufficient"
    result = PitchInterpretationEligibility.model_validate(
        dict(state=state, reasons=tuple(reasons), metrics=m)
    )
    # A proven short candidate branch is excluded evidence, not an unresolved
    # competing path. Recheck the independently retained region; preserve ALL raw
    # metrics above for audit. No other quality rejection receives this waiver.
    from benma_api.pronunciation.pitch_rejection import BRANCH_REASON

    certified = [f for f in raw if BRANCH_REASON in f.exclusion_reasons]
    other_missing = [f for f in raw if f.selected_f0_hz is None and f not in certified]
    if (
        _interpretation_raw is None
        and certified
        and selected
        and track.raw_provenance == "native_tracker"
        and len(selected) >= 2 * len(certified)
        and len(other_missing) <= 1
        and all(
            set(f.exclusion_reasons) <= {"below_energy_gate", "missing_or_out_of_range_f0"}
            and "below_energy_gate" in f.exclusion_reasons
            for f in other_missing
        )
    ):
        # Bound attrition again in the projected unit; a short fragment of the
        # primary cannot inherit the full recording's branch certificate.
        checked = interpretation_eligibility(track, region, _interpretation_raw=selected)
        if checked.state == "sufficient":
            return result.model_copy(
                update={
                    "state": "sufficient",
                    "reasons": ("candidate_branch_excluded_primary_sufficient",),
                }
            )
    return result


def gate_observation(
    observed: ObservedContour, eligibility: PitchInterpretationEligibility
) -> ObservedContour:
    if eligibility.state == "sufficient":
        return observed
    return ObservedContour(
        reason="pitch_evidence_" + eligibility.state,
        voiced_coverage=observed.voiced_coverage,
        features=observed.features,
    )

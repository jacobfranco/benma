"""Reliable pitch evidence, conservative shape classification, and display views.

Never modifies raw F0, never octave-corrects, and never interpolates. A local
Hampel test rejects isolated >6 st deviations only with support on both sides.
Sustained high/low pitch survives. Median-of-three smoothing stays within each
voiced region. The classifier derives its evidence from raw frames, never from
the caller's display geometry. Neither filtering nor shape thresholds are
calibrated pronunciation scores.
"""

from __future__ import annotations

import math
import statistics
import time
from itertools import pairwise
from typing import Any

from benma_api.pronunciation.evidence_region import select_tone_evidence
from benma_api.schemas import DisplayContour, DisplayPitchPoint, ObservedContour

MAX_GAP = 0.045  # Missing/unvoiced frames always break a segment, even below this limit.
CLASSIFIER_VERSION = "acoustic-shape-quality-v7-bounded-gestures"
DISPLAY_VERSION = "local-hampel-short-island-no-interpolation-v2.1"


def display_contour(raw: list[dict[str, Any]]) -> DisplayContour:
    """Display view of reliable measured pitch; downstream smoothing is display-only."""
    return _reliable_pitch_contour(raw)


def _reliable_pitch_contour(raw: list[dict[str, Any]]) -> DisplayContour:
    """Full-resolution evidence, encoded in the existing contour transport type."""
    valid: list[tuple[float, float] | None] = []
    for point in raw:
        t, hz, confidence = (
            point.get("timestamp_seconds"),
            point.get("f0_hz"),
            point.get("voicing_probability"),
        )
        usable = (
            point.get("quality_usable", True)
            and isinstance(t, (int, float))
            and math.isfinite(t)
            and t >= 0
            and isinstance(hz, (int, float))
            and math.isfinite(hz)
            and 40 <= hz <= 1000
            and (confidence is None or confidence >= 0.45)
        )
        if usable:
            assert isinstance(t, (int, float)) and isinstance(hz, (int, float))
            valid.append((float(t), float(hz)))
        else:
            valid.append(None)
    baseline = statistics.median([p[1] for p in valid if p]) if any(valid) else None
    if baseline is None:
        return DisplayContour(method=DISPLAY_VERSION)
    values = [12 * math.log2(p[1] / baseline) if p else None for p in valid]
    rejected: set[int] = set()
    # Brief octave islands bracketed by agreeing pitch are not reliable display
    # evidence. Drop them, never shift frequencies or fill the resulting gaps.
    regions: list[list[int]] = []
    for i, sample in enumerate(valid):
        if sample is None:
            continue
        previous = valid[i - 1] if i else None
        if (
            previous is None
            or sample[0] - previous[0] > MAX_GAP
            or abs(12 * math.log2(sample[1] / previous[1])) > 6
        ):
            regions.append([])
        regions[-1].append(i)
    for preceding, middle, following in zip(regions, regions[1:], regions[2:], strict=False):
        a, b, c, d = valid[preceding[-1]], valid[middle[0]], valid[middle[-1]], valid[following[0]]
        assert a and b and c and d
        if c[0] - b[0] <= 0.08 and b[0] - a[0] <= 0.12 and d[0] - c[0] <= 0.12:
            before = statistics.median([v for i in preceding[-5:] if (v := values[i]) is not None])
            inside = statistics.median([v for i in middle if (v := values[i]) is not None])
            after = statistics.median([v for i in following[:5] if (v := values[i]) is not None])
            if abs(before - after) <= 2 and abs(inside - before) > 6 and abs(inside - after) > 6:
                rejected.update(middle)
    for i, value in enumerate(values):
        if value is None:
            continue
        # A local region must be contiguous and contain evidence on both sides.
        left: list[float | None] = []
        right: list[float | None] = []
        for direction, neighbors in ((-1, left), (1, right)):
            previous = valid[i]
            for distance in range(1, 4):
                j = i + direction * distance
                if not 0 <= j < len(valid) or valid[j] is None:
                    break
                current = valid[j]
                assert previous is not None and current is not None
                if not 0 < abs(current[0] - previous[0]) <= MAX_GAP:
                    break
                neighbors.append(values[j])
                previous = current
        local_values = [v for v in left + right if v is not None]
        if len(left) < 2 or len(right) < 2:
            continue
        median = statistics.median(local_values)
        mad = statistics.median(abs(v - median) for v in local_values)
        if abs(value - median) > max(6, 3 * 1.4826 * mad):
            rejected.add(i)
    # Recompute the display baseline after rejecting artifacts, leaving raw normalization intact.
    retained_hz = [p[1] for i, p in enumerate(valid) if p and i not in rejected]
    baseline = statistics.median(retained_hz) if retained_hz else baseline
    segments: list[list[DisplayPitchPoint]] = []
    segment: list[DisplayPitchPoint] = []
    for i, sample in enumerate(valid):
        if sample is None or i in rejected:
            if segment:
                segments.append(segment)
            segment = []
            continue
        t, hz = sample
        if segment and not 0 < t - segment[-1].timestamp_seconds <= MAX_GAP:
            segments.append(segment)
            segment = []
        segment.append(
            DisplayPitchPoint(
                timestamp_seconds=t, normalized_semitones=12 * math.log2(hz / baseline)
            )
        )
    if segment:
        segments.append(segment)
    smoothed: list[list[DisplayPitchPoint]] = []
    for region in segments:
        smoothed.append(
            [
                DisplayPitchPoint(
                    timestamp_seconds=p.timestamp_seconds,
                    normalized_semitones=round(
                        statistics.median([v.normalized_semitones for v in region[i - 1 : i + 2]])
                        if 0 < i < len(region) - 1
                        else p.normalized_semitones,
                        4,
                    ),
                )
                for i, p in enumerate(region)
            ]
        )
    heights = [p.normalized_semitones for region in smoothed for p in region]
    return DisplayContour(
        method=DISPLAY_VERSION,
        segments=smoothed,
        baseline_hz=round(baseline, 3),
        minimum_semitones=min(-3, min(heights, default=0) - 1),
        maximum_semitones=max(3, max(heights, default=0) + 1),
        rejected_points=len(rejected)
        + sum(point.get("f0_hz") is not None and valid[i] is None for i, point in enumerate(raw)),
    )


def syllable_contour(contour: DisplayContour, start: float, end: float) -> DisplayContour:
    return contour.model_copy(
        update={
            "segments": [
                selected
                for region in contour.segments
                if (selected := [p for p in region if start <= p.timestamp_seconds < end])
            ]
        }
    )


def simplify_display(
    contour: DisplayContour, tolerance: float = 0.15, *, preserve_seconds: float | None = None
) -> DisplayContour:
    """Retain measured vertices within 0.15 st error; never bridge voiced segments.

    Classification uses the full-resolution display contour BEFORE simplification.
    This bounds native View count for long recordings, without inventing samples.
    """
    simplified: list[list[DisplayPitchPoint]] = []
    for segment in contour.segments:
        if not segment:
            continue
        keep = {0, len(segment) - 1}
        if preserve_seconds is not None:
            keep.update(
                i
                for i, p in enumerate(segment)
                if abs(p.timestamp_seconds - preserve_seconds) <= 0.000051
            )
        pending = list(pairwise(sorted(keep)))
        while pending:
            first, last = pending.pop()
            a, b = segment[first], segment[last]
            if last - first < 2:
                continue
            span = b.timestamp_seconds - a.timestamp_seconds
            deviations = [
                (
                    abs(
                        p.normalized_semitones
                        - (
                            a.normalized_semitones
                            + (b.normalized_semitones - a.normalized_semitones)
                            * (p.timestamp_seconds - a.timestamp_seconds)
                            / span
                        )
                    ),
                    i,
                )
                for i in range(first + 1, last)
                if (p := segment[i])
            ]
            error, index = max(deviations)
            if error > tolerance:
                keep.add(index)
                pending.extend(((first, index), (index, last)))
        simplified.append([segment[i] for i in sorted(keep)])
    return contour.model_copy(update={"segments": simplified})


def classify_contour(
    contour: DisplayContour,
    start: float,
    end: float,
    *,
    raw: list[dict[str, Any]],
    timing_reliable: bool = True,
    timings: dict[str, float] | None = None,
) -> ObservedContour:
    started = time.perf_counter()
    stages: dict[str, float] = {}
    # Keep the positional argument for existing local tooling, but do not trust
    # a simplified, normalized, or otherwise modified display as acoustic truth.
    del contour
    region = select_tone_evidence(raw, start, end) if timing_reliable else None
    evidence = _reliable_pitch_contour(raw)
    result = _classify_contour(
        evidence,
        region.start if region else start,
        region.end if region else end,
        raw=raw,
        timing_reliable=timing_reliable,
        stages=stages,
    )
    if region and region.selected:
        # A second whole-span derivation is diagnostic only. It cannot select
        # the interval, change the region's category or veto its quality.
        whole = _classify_contour(
            evidence,
            start,
            end,
            raw=raw,
            timing_reliable=timing_reliable,
            stages={},
        )
        result.features.update(
            {f"whole_span_{key}": value for key, value in whole.features.items()}
        )
        result.features.update(
            {
                "evidence_region_selected": 1.0,
                "evidence_start_seconds": round(region.start, 4),
                "evidence_end_seconds": round(region.end, 4),
                "excluded_onset_frames": float(region.onset_frames),
                "excluded_terminal_frames": float(region.terminal_frames),
                "evidence_coverage": result.voiced_coverage,
                "evidence_duration_seconds": round(region.end - region.start, 4),
                "full_span_coverage": whole.features.get("full_span_coverage", 0),
                "duration_seconds": round(end - start, 4),
                "alignment_start_seconds": start,
                "alignment_end_seconds": end,
            }
        )
        # Keep the public historical coverage denominator; grading features
        # above describe the explicit region. Whole-span diagnostics stay separate.
        result.voiced_coverage = whole.voiced_coverage
    elapsed = (time.perf_counter() - started) * 1000
    gate = stages.get("quality_gate", elapsed)
    if timings is not None:
        timings["quality_gate"] = timings.get("quality_gate", 0) + gate
        timings["observed_classification"] = timings.get("observed_classification", 0) + max(
            0, elapsed - gate
        )
    return result


def _classify_contour(
    contour: DisplayContour,
    start: float,
    end: float,
    *,
    raw: list[dict[str, Any]],
    timing_reliable: bool = True,
    stages: dict[str, float],
) -> ObservedContour:
    started = time.perf_counter()
    if not timing_reliable:
        return ObservedContour(reason="synthetic_timing")
    duration = end - start
    contour = syllable_contour(contour, start, end)
    points = [p for region in contour.segments for p in region]
    raw_voiced = [
        p
        for p in raw
        if start <= p.get("timestamp_seconds", -1) < end and p.get("f0_hz") is not None
    ]
    intervals = [
        b.timestamp_seconds - a.timestamp_seconds
        for region in contour.segments
        for a, b in pairwise(region)
    ]
    hop = min(0.02, statistics.median(intervals)) if intervals else 0.01
    coverage = (
        min(
            1.0,
            sum(
                region[-1].timestamp_seconds - region[0].timestamp_seconds + hop
                for region in contour.segments
            )
            / duration,
        )
        if duration > 0
        else 0
    )
    # Timing margins are tolerated only at the boundaries, with a hard cap.
    # Full-span coverage remains the public provenance metric. A tiny lock in
    # a long span cannot become sufficient evidence simply by trimming to itself.
    first_time = points[0].timestamp_seconds if points else start
    last_time = points[-1].timestamp_seconds if points else start
    leading = max(0.0, first_time - start) if points else 0.0
    trailing = max(0.0, end - last_time - hop) if points else 0.0
    voiced_duration = coverage * max(0.0, duration)
    core_duration = last_time - first_time + hop if points else 0.0
    boundary_duration = max(hop, duration - min(0.15, leading) - min(0.15, trailing))
    core_coverage = min(1.0, voiced_duration / core_duration) if core_duration > 0 else 0.0
    boundary_coverage = min(1.0, voiced_duration / boundary_duration)
    unclear = ObservedContour(reason="insufficient_voicing", voiced_coverage=round(coverage, 3))
    contaminated = sum(
        p.get("low_frequency_contaminated", p.get("quality_usable") is False) for p in raw_voiced
    )
    gaps = []
    for left, right in pairwise(contour.segments):
        a, b = left[-1], right[0]
        gap = b.timestamp_seconds - a.timestamp_seconds
        delta_gap = b.normalized_semitones - a.normalized_semitones
        # A short dropout in an ongoing rise/fall is compatible with the locally
        # measured velocity. This predicts only an endpoint, never missing F0.
        slopes = [
            (y.normalized_semitones - x.normalized_semitones)
            / (y.timestamp_seconds - x.timestamp_seconds)
            for region in (left[-4:], right[:4])
            for x, y in pairwise(region)
            if y.timestamp_seconds > x.timestamp_seconds
        ]
        predicted = statistics.median(slopes) * gap if len(slopes) >= 4 else 0.0
        residual = min(abs(delta_gap), abs(delta_gap - predicted))
        gaps.append((gap, residual))
    quality = {
        "gap_count": float(len(gaps)),
        "longest_gap_seconds": max((gap for gap, _ in gaps), default=0.0),
        "discontinuous_gap_count": float(sum(change > 1.5 for _, change in gaps)),
        "first_retained_seconds": first_time,
        "last_retained_seconds": last_time,
        "alignment_start_seconds": start,
        "alignment_end_seconds": end,
        "full_span_coverage": coverage,
        "duration_seconds": duration,
        "raw_voiced_frames": float(len(raw_voiced)),
        "retained_display_frames": float(len(points)),
        "voiced_duration_seconds": voiced_duration,
        "active_core_duration_seconds": core_duration,
        "active_core_coverage": core_coverage,
        "boundary_tolerant_coverage": boundary_coverage,
        "leading_padding_seconds": leading,
        "trailing_padding_seconds": trailing,
        "contaminated_fraction": contaminated / len(raw_voiced) if raw_voiced else 0.0,
    }
    if raw_voiced:
        quality["first_raw_voiced_seconds"] = raw_voiced[0]["timestamp_seconds"]
        quality["last_raw_voiced_seconds"] = raw_voiced[-1]["timestamp_seconds"]
    jumps = [
        abs(12 * math.log2(b["f0_hz"] / a["f0_hz"]))
        for a, b in pairwise(raw_voiced)
        if a["f0_hz"] > 0
        and b["f0_hz"] > 0
        and 0 < b["timestamp_seconds"] - a["timestamp_seconds"] <= 0.12
    ]
    quality["maximum_tracker_jump_st"] = max(jumps, default=0.0)
    large_count = sum(jump > 6 for jump in jumps)
    longest_run = run = 0
    for jump in jumps:
        run = run + 1 if jump > 6 else 0
        longest_run = max(longest_run, run)
    retained_times = {p.timestamp_seconds for p in points}
    unexplained = sum(
        abs(12 * math.log2(b["f0_hz"] / a["f0_hz"])) > 6
        and a["timestamp_seconds"] in retained_times
        and b["timestamp_seconds"] in retained_times
        for a, b in pairwise(raw_voiced)
        if a["f0_hz"] > 0
        and b["f0_hz"] > 0
        and 0 < b["timestamp_seconds"] - a["timestamp_seconds"] <= 0.12
    )
    quality.update(
        {
            "large_jump_count": float(large_count),
            "large_jump_fraction": large_count / len(jumps) if jumps else 0.0,
            "longest_unstable_run": float(longest_run),
            "octave_like_jump_count": float(sum(9 <= jump <= 15 for jump in jumps)),
            "retained_after_filter_count": float(len(points)),
            "instability_density_per_second": large_count / core_duration if core_duration else 0.0,
            "unexplained_large_jump_count": float(unexplained),
            "isolated_filtered_glitch": 0.0,
            "tracker_instability_rejected": float(large_count > 0),
        }
    )
    # Retain diagnostic shape features even when quality rejects a label.
    # Broad movement is measured over five equal-count median bins; cycle-to-cycle
    # jitter is checked separately. No target or expected tone enters this function.
    full_values = [p.normalized_semitones for p in points]
    if len(points) < 5:
        # No synthetic zero-valued shape features for absent/insufficient pitch.
        reason = "insufficient_voicing"
        if quality["contaminated_fraction"] >= 0.15:
            reason = "low_frequency_contamination"
        elif quality["maximum_tracker_jump_st"] > 6:
            reason = "tracker_instability"
        return unclear.model_copy(
            update={"reason": reason, "features": {k: round(v, 4) for k, v in quality.items()}}
        )
    values = [
        statistics.median(full_values[i * len(points) // 5 : (i + 1) * len(points) // 5])
        for i in range(5)
    ]
    # Local residual noise does not grow simply because a vowel is longer.
    residuals = sorted(
        abs(
            p.normalized_semitones
            - statistics.median(q.normalized_semitones for q in region[max(0, i - 2) : i + 3])
        )
        for region in contour.segments
        for i, p in enumerate(region)
    )
    residual_p90 = (
        residuals[min(len(residuals) - 1, int(len(residuals) * 0.9))] if residuals else 0.0
    )
    raw_residuals = sorted(
        abs(
            12 * math.log2(p["f0_hz"])
            - statistics.median(
                12 * math.log2(q["f0_hz"])
                for q in raw_voiced[max(0, i - 2) : i + 3]
                if q["f0_hz"] > 0 and abs(q["timestamp_seconds"] - p["timestamp_seconds"]) <= 0.025
            )
        )
        for i, p in enumerate(raw_voiced)
        if p["f0_hz"] > 0
    )
    raw_residual_p90 = (
        raw_residuals[min(len(raw_residuals) - 1, int(len(raw_residuals) * 0.9))]
        if raw_residuals
        else 0.0
    )
    # Compare raw and filtered shape at shared timestamps, relative to the same
    # baseline. Removed frames are counted separately, never octave-corrected.
    raw_by_time = {p["timestamp_seconds"]: p["f0_hz"] for p in raw_voiced}
    disagreement = [
        abs(
            12 * math.log2(raw_by_time[p.timestamp_seconds] / contour.baseline_hz)
            - p.normalized_semitones
        )
        for p in points
        if contour.baseline_hz and raw_by_time.get(p.timestamp_seconds, 0) > 0
    ]
    quality["raw_filtered_disagreement_mean_st"] = (
        statistics.mean(disagreement) if disagreement else 0.0
    )
    edge = 1
    first, last = statistics.median(values[:edge]), statistics.median(values[-edge:])
    low, high = min(values), max(values)
    low_index = values.index(low)
    low_position = low_index / (len(values) - 1)
    delta = last - first
    movement = sum(abs(b - a) for a, b in pairwise(values))
    span = high - low
    retained_jump = max(
        (abs(b.normalized_semitones - a.normalized_semitones) for a, b in pairwise(points)),
        default=0.0,
    )
    # A single removed island has at most two entry/exit jumps. All large
    # transitions must touch discarded evidence; robust bins alone cannot hide
    # an unfiltered octave step. Repeated glitches and disconnected cores fail.
    isolated_glitch = (
        0 < large_count <= 2
        and quality["large_jump_fraction"] <= 0.10
        and unexplained == 0
        and 0 < len(raw_voiced) - len(points) <= max(1, len(raw_voiced) * 0.10)
        and len(contour.segments) <= 2
        and core_coverage >= 0.95
        and max(
            (b.timestamp_seconds - a.timestamp_seconds for a, b in pairwise(points)), default=0.0
        )
        <= 0.045
        and retained_jump <= 1.5
        and residual_p90 <= 0.5
        and raw_residual_p90 <= 0.5
        and quality["raw_filtered_disagreement_mean_st"] <= 0.5
        and movement <= max(1.5, span * 1.5)
    )
    quality["isolated_filtered_glitch"] = float(isolated_glitch)
    quality["tracker_instability_rejected"] = float(large_count > 0 and not isolated_glitch)
    quality["maximum_retained_jump_st"] = retained_jump
    # A discontinuous endpoint is not necessarily a contradictory branch. This
    # exception reasons over two observed segments, never fills the missing F0.
    # Ordinary continuous/small-residual gaps keep their existing policy.
    coherent_gap = False
    if (
        len(gaps) == 1
        and quality["discontinuous_gap_count"] == 1
        and 0 < gaps[0][0] <= 0.04
        and core_coverage >= 0.9
        and gaps[0][0] - hop <= core_duration * 0.1
        and all(len(segment) >= 6 for segment in contour.segments)
        and len(points) == len(raw_voiced)
        and contaminated == 0
        and large_count == 0
        and residual_p90 <= 0.75
        and raw_residual_p90 <= 0.75
        and quality["raw_filtered_disagreement_mean_st"] <= 0.25
        and abs(delta) >= 2
    ):
        direction = 1 if delta > 0 else -1
        segment_bins = [
            [
                statistics.median(
                    p.normalized_semitones
                    for p in segment[i * len(segment) // 3 : (i + 1) * len(segment) // 3]
                )
                for i in range(3)
            ]
            for segment in contour.segments
        ]
        left, right = contour.segments
        gap_delta = right[0].normalized_semitones - left[-1].normalized_semitones
        # Require independent raw/high-pass agreement and strong periodicity on
        # both sides. A missing or competing octave estimate cannot certify this.
        flank_times = {p.timestamp_seconds for p in left[-3:] + right[:3]}
        flanks = [p for p in raw_voiced if p["timestamp_seconds"] in flank_times]
        coherent_gap = (
            gap_delta * direction > 0
            and all((b - a) * direction >= -0.25 for a, b in pairwise(values))
            and all(
                (bins[-1] - bins[0]) * direction >= 0.5
                and all((b - a) * direction >= -0.25 for a, b in pairwise(bins))
                for bins in segment_bins
            )
            and all(
                isinstance(p.get("voicing_probability"), (int, float))
                and p["voicing_probability"] >= 0.65
                and p.get("comparison_f0_hz")
                and abs(12 * math.log2(p["f0_hz"] / p["comparison_f0_hz"])) <= 0.5
                for p in flanks
            )
        )
    quality["coherent_short_gap"] = float(coherent_gap)
    features = {
        **quality,
        **{f"bin_{i + 1}_st": value for i, value in enumerate(values)},
        # Representative observed times for display-only summaries. These do
        # not enter any quality gate or category decision.
        **{
            f"bin_{i + 1}_seconds": statistics.median(
                p.timestamp_seconds
                for p in points[i * len(points) // 5 : (i + 1) * len(points) // 5]
            )
            for i in range(5)
        },
        "local_residual_p90_st": residual_p90,
        "raw_local_residual_p90_st": raw_residual_p90,
        "start_st": first,
        "end_st": last,
        "change_st": delta,
        "range_st": span,
        "minimum_position": low_position,
        "pre_minimum_fall_st": first - low,
        "post_minimum_recovery_st": last - low,
        "duration_seconds": duration,
        "path_length_st": movement,
        "frame_path_length_st": sum(abs(b - a) for a, b in pairwise(full_values)),
    }
    # A reliable core is a derived classification hypothesis, not a phonetic
    # nucleus alignment. Only a brief edge followed by a long, level plateau
    # qualifies; never flatten an interior valley, rebound or sustained fall.
    core_points = points
    if len(contour.segments) == 1 and len(points) >= 15:
        for cut in range(1, int(len(points) * 0.3) + 1):
            candidate = points[cut:]
            tail = [p.normalized_semitones for p in candidate]
            bins = [
                statistics.median(tail[i * len(tail) // 5 : (i + 1) * len(tail) // 5])
                for i in range(5)
            ]
            if (
                len(candidate) >= 14
                and candidate[-1].timestamp_seconds - candidate[0].timestamp_seconds + hop >= 0.14
                and candidate[0].timestamp_seconds - first_time <= 0.08
                and max(tail) - min(tail) <= 1.25
                and max(bins) - min(bins) <= 0.75
                and abs(full_values[0] - bins[0]) >= 1.5
            ):
                core_points = candidate
                break
    core_values = [p.normalized_semitones for p in core_points]
    core_bins = [
        statistics.median(core_values[i * len(core_values) // 5 : (i + 1) * len(core_values) // 5])
        for i in range(5)
    ]
    onset_core = len(core_points) < len(points)
    periodicity = [p.get("voicing_probability") for p in raw_voiced]
    # A duration exception alone would still leave a 1.7 st fall ambiguous.
    # This separate low-confidence rule requires stronger evidence than the
    # ordinary gate and deliberately does not admit short levels or rises.
    short_fall = (
        0.10 - 1e-9 <= voiced_duration < 0.12
        and len(points) >= 10
        and len(contour.segments) == 1
        and len(points) == len(raw_voiced)
        and core_coverage >= 0.98
        and boundary_coverage >= 0.65
        and quality["contaminated_fraction"] == 0
        and quality["maximum_tracker_jump_st"] <= 1
        and residual_p90 <= 0.5
        and raw_residual_p90 <= 0.5
        and all(isinstance(p, (int, float)) and p >= 0.55 for p in periodicity)
        and statistics.median(p for p in periodicity if isinstance(p, (int, float))) >= 0.7
        and delta <= -1.5
        and movement <= abs(delta) * 1.1
        and sum(abs(b - a) for a, b in pairwise(full_values))
        <= abs(full_values[-1] - full_values[0]) * 1.15
    )
    features.update(
        {
            **{f"core_bin_{i + 1}_st": value for i, value in enumerate(core_bins)},
            **{
                f"core_bin_{i + 1}_seconds": statistics.median(
                    p.timestamp_seconds
                    for p in core_points[
                        i * len(core_points) // 5 : (i + 1) * len(core_points) // 5
                    ]
                )
                for i in range(5)
            },
            "first_reliable_core_seconds": core_points[0].timestamp_seconds,
            "last_reliable_core_seconds": core_points[-1].timestamp_seconds,
            "reliable_core_duration_seconds": core_points[-1].timestamp_seconds
            - core_points[0].timestamp_seconds
            + hop,
            "reliable_core_frames": float(len(core_points)),
            "reliable_core_coverage": 1.0 if onset_core else core_coverage,
            "onset_transient_magnitude_st": abs(full_values[0] - core_bins[0]) if onset_core else 0,
            "stable_start_st": core_bins[0],
            "stable_end_st": core_bins[-1],
            "core_change_st": core_bins[-1] - core_bins[0],
            "full_change_st": delta,
            "onset_core_candidate": float(onset_core),
            "short_fall_candidate": float(short_fall),
        }
    )
    unclear.features = {k: round(v, 4) for k, v in features.items()}
    if quality["contaminated_fraction"] >= 0.15:
        return unclear.model_copy(update={"reason": "low_frequency_contamination"})
    if quality["tracker_instability_rejected"]:
        return unclear.model_copy(update={"reason": "tracker_instability"})
    if (
        duration < 0.12
        or duration > 1.5
        or len(points) < 8
        or (voiced_duration < 0.12 and not short_fall)
        or boundary_coverage < 0.5
        or core_coverage < 0.8
    ):
        return unclear
    if len(raw_voiced) and len(points) / len(raw_voiced) < 0.8:
        return unclear.model_copy(update={"reason": "noisy_contour"})
    if (
        not intervals
        or (quality["discontinuous_gap_count"] > 0 and not coherent_gap)
        or max((b.timestamp_seconds - a.timestamp_seconds for a, b in pairwise(points)), default=0)
        > 0.09
    ):
        return unclear.model_copy(update={"reason": "fragmented_voicing"})
    stages["quality_gate"] = (time.perf_counter() - started) * 1000
    # Broad zigzags and local jitter are different evidence. Raw path is kept
    # for inspection, but no longer penalizes long, coherent contours by itself.
    if movement > max(3.5, 2.2 * span) or residual_p90 > 0.75 or raw_residual_p90 > 1.5:
        return unclear.model_copy(update={"reason": "noisy_contour"})
    if onset_core or short_fall:
        return ObservedContour(
            classification="1-like" if onset_core else "4-like",
            confidence="low",
            reason="sustained_level_after_onset" if onset_core else "short_coherent_fall",
            voiced_coverage=round(coverage, 3),
            features=unclear.features,
        )
    label: str | None = None
    # Weak valleys need stronger structural evidence than the canonical rule:
    # an interior trough with two broad steps on each limb, a meaningful fall
    # and recovery, and little reversal. An early onset sag remains a rise.
    shallow_valley = (
        low_index == 2
        and first - low >= 1.0
        and last - low >= 1.0
        and min(first - low, last - low) >= movement * 0.25
        and values[0] > values[1] > values[2] < values[3] < values[4]
        and residual_p90 <= 0.35
        and raw_residual_p90 <= 0.5
        and quality["raw_filtered_disagreement_mean_st"] <= 0.25
        and len(contour.segments) == 1
        and core_coverage >= 0.95
        and voiced_duration >= 0.2
    )
    if span <= 1.5 and abs(delta) <= 1:
        label = "1-like"
    elif delta >= 2 and first - low < 1.5 and low_position <= 0.5 and movement <= delta * 1.8:
        # A minor onset sag is compatible with a rise; a substantial valley is not.
        label = "2-like"
    elif 0.2 <= low_position <= 0.8 and first - low >= 1.5 and last - low >= 1.5:
        label = "3-like"
    elif delta <= -2 and movement <= abs(delta) * 1.8:
        label = "4-like"
    elif shallow_valley:
        return ObservedContour(
            classification="3-like",
            confidence="low",
            reason="shallow_coherent_valley",
            voiced_coverage=round(coverage, 3),
            features=unclear.features,
        )
    if label is None:
        return unclear.model_copy(update={"reason": "ambiguous_shape"})
    return ObservedContour.model_validate(
        {
            "classification": label,
            "confidence": "low" if isolated_glitch or coherent_gap else "moderate",
            "reason": "isolated_filtered_glitch"
            if isolated_glitch
            else "coherent_short_gap"
            if coherent_gap
            else "acoustic_shape_only",
            "voiced_coverage": round(coverage, 3),
            "features": unclear.features,
        }
    )

"""Display-only robust pitch and conservative acoustic shape classification.

Never modifies raw F0, never octave-corrects, and never interpolates. A local
Hampel test rejects isolated >6 st deviations only with support on both sides.
Sustained high/low pitch survives. Median-of-three smoothing stays within each
voiced region. Thresholds are visualization heuristics, not calibrated scores.
"""

from __future__ import annotations

import math
import statistics
import time
from itertools import pairwise
from typing import Any

from benma_api.schemas import DisplayContour, DisplayPitchPoint, ObservedContour

MAX_GAP = 0.045  # Missing/unvoiced frames always break a segment, even below this limit.
CLASSIFIER_VERSION = "acoustic-shape-quality-v2"
DISPLAY_VERSION = "local-hampel-short-island-no-interpolation-v2.1"


def display_contour(raw: list[dict[str, Any]]) -> DisplayContour:
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


def simplify_display(contour: DisplayContour, tolerance: float = 0.15) -> DisplayContour:
    """Retain measured vertices within 0.15 st error; never bridge voiced segments.

    Classification uses the full-resolution display contour BEFORE simplification.
    This bounds native View count for long recordings, without inventing samples.
    """
    simplified: list[list[DisplayPitchPoint]] = []
    for segment in contour.segments:
        if not segment:
            continue
        keep = {0, len(segment) - 1}
        pending = [(0, len(segment) - 1)]
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
    result = _classify_contour(
        contour, start, end, raw=raw, timing_reliable=timing_reliable, stages=stages
    )
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
    unclear = ObservedContour(reason="insufficient_voicing", voiced_coverage=round(coverage, 3))
    contaminated = sum(p.get("quality_usable") is False for p in raw_voiced)
    quality = {
        "duration_seconds": duration,
        "raw_voiced_frames": float(len(raw_voiced)),
        "contaminated_fraction": contaminated / len(raw_voiced) if raw_voiced else 0.0,
    }
    jumps = [
        abs(12 * math.log2(b["f0_hz"] / a["f0_hz"]))
        for a, b in pairwise(raw_voiced)
        if 0 < b["timestamp_seconds"] - a["timestamp_seconds"] <= 0.12
    ]
    quality["maximum_tracker_jump_st"] = max(jumps, default=0.0)
    unclear.features = {k: round(v, 4) for k, v in quality.items()}
    if quality["contaminated_fraction"] >= 0.15:
        return unclear.model_copy(update={"reason": "low_frequency_contamination"})
    if quality["maximum_tracker_jump_st"] > 6:
        return unclear.model_copy(update={"reason": "tracker_instability"})
    if duration < 0.12 or duration > 1.5 or len(points) < 8 or coverage < 0.5:
        return unclear
    if len(raw_voiced) and len(points) / len(raw_voiced) < 0.8:
        return unclear.model_copy(update={"reason": "noisy_contour"})
    if (
        not intervals
        or max(
            (b.timestamp_seconds - a.timestamp_seconds for a, b in pairwise(points)),
            default=0,
        )
        > 0.09
    ):
        return unclear.model_copy(update={"reason": "fragmented_voicing"})
    stages["quality_gate"] = (time.perf_counter() - started) * 1000
    # Broad movement is measured over five robust time bins; cycle-to-cycle
    # jitter is checked separately. No target or expected tone enters this function.
    full_values = [p.normalized_semitones for p in points]
    values = [
        statistics.median(full_values[i * len(points) // 5 : (i + 1) * len(points) // 5])
        for i in range(5)
    ]
    edge = 1
    first, last = statistics.median(values[:edge]), statistics.median(values[-edge:])
    low, high = min(values), max(values)
    low_index = values.index(low)
    low_position = low_index / (len(values) - 1)
    delta = last - first
    movement = sum(abs(b - a) for a, b in pairwise(values))
    span = high - low
    features = {
        **quality,
        "start_st": first,
        "end_st": last,
        "change_st": delta,
        "range_st": span,
        "minimum_position": low_position,
        "duration_seconds": duration,
        "path_length_st": movement,
        "frame_path_length_st": sum(abs(b - a) for a, b in pairwise(full_values)),
    }
    unclear.features = {k: round(v, 4) for k, v in features.items()}
    # Jagged paths can masquerade as either endpoint slope or a valley.
    if movement > max(3.5, 2.2 * span) or features["frame_path_length_st"] > max(8, 4 * span):
        return unclear.model_copy(update={"reason": "noisy_contour"})
    label: str | None = None
    if span <= 1.5 and abs(delta) <= 1:
        label = "1-like"
    elif 0.2 <= low_position <= 0.8 and first - low >= 1.5 and last - low >= 1.5:
        label = "3-like"
    elif delta >= 2 and movement <= abs(delta) * 1.8:
        label = "2-like"
    elif delta <= -2 and movement <= abs(delta) * 1.8:
        label = "4-like"
    if label is None:
        return unclear.model_copy(update={"reason": "ambiguous_shape"})
    return ObservedContour.model_validate(
        {
            "classification": label,
            "confidence": "moderate",
            "reason": "acoustic_shape_only",
            "voiced_coverage": round(coverage, 3),
            "features": unclear.features,
        }
    )

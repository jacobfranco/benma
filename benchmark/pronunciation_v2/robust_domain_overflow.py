"""Research-only Mine DISPLAY windows and truthful screen-space overflow.

No pitch selection, correction, centering, timing inference, or classification.
Inputs are already selected, recording-baseline semitones with real continuity.
"""

from __future__ import annotations

import math
import statistics
from itertools import pairwise

POLICIES = ("q90", "q95", "q97.5", "mad3")


def quantile(values, fraction):
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    left = math.floor(index)
    return ordered[left] + (ordered[math.ceil(index)] - ordered[left]) * (index - left)


def derive_mine_display_domain(segments, policy):
    """One linear utterance window. Existing ±3 minimum and 1 st padding.

    Quantiles use all owned measured samples, never simplified vertices.
    MAD uses the conventional normal-consistent 1.4826 factor, bounded by
    the complete padded range so robust spread cannot zoom OUT farther.
    This is a display estimator, not a definition of acoustic normality.
    """
    if policy not in POLICIES:
        raise ValueError("unknown display policy")
    values = [p["normalized_semitones"] for seg in segments for p in seg]
    if not all(math.isfinite(v) for v in values):
        raise ValueError("finite selected values required; never silently reject")
    if not values:
        return [-3.0, 3.0]
    if policy.startswith("q"):
        tail = (1 - float(policy[1:]) / 100) / 2
        low, high = quantile(values, tail), quantile(values, 1 - tail)
    else:
        median = statistics.median(values)
        spread = 1.4826 * statistics.median(abs(v - median) for v in values)
        low, high = max(min(values), median - 3 * spread), min(max(values), median + 3 * spread)
    return [min(-3.0, low - 1), max(3.0, high + 1)]


def project_with_overflow(segments, domain, units, cadence):
    """Clip ONLY derived line geometry; preserve every source object.

    Boundary endpoints are interpolated in both time and cell position.
    One dashed duration rail + outward chevron represents each outside run.
    Separate input segments always end paths AND overflow events.

    Support convention: linear between consecutive selected samples; half-hop
    constant endpoint support clipped to the accepted unit. Endpoint support
    is for the diagnostic duration/rail only, never a fabricated contour line.
    """
    low, high = domain
    if not (math.isfinite(low) and math.isfinite(high) and high > low and cadence > 0):
        raise ValueError("invalid display domain or cadence")
    unit_map = {u["key"]: u for u in units}
    paths, events, crossings = [], [], []
    total_support = 0.0

    def side(value):
        return "below" if value < low else "above" if value > high else "inside"

    def vertex(point):
        return {k: point[k] for k in ("timestamp_seconds", "position", "normalized_semitones")}

    for segment_index, segment in enumerate(segments):
        if not segment:
            continue
        unit = unit_map[segment[0]["unit_key"]]
        support_start = max(unit["start_seconds"], segment[0]["timestamp_seconds"] - cadence / 2)
        support_end = min(unit["end_seconds"], segment[-1]["timestamp_seconds"] + cadence / 2)
        total_support += support_end - support_start
        path = None
        event = None

        def append_piece(kind, a, b, segment_index=segment_index, unit=unit):
            nonlocal path, event
            if kind == "inside":
                event = None
                if path is None:
                    path = [a]
                    paths.append(path)
                if path[-1] != b:
                    path.append(b)
            else:
                path = None
                if event is None or event["side"] != kind:
                    event = dict(
                        segment_index=segment_index,
                        unit_key=unit["key"],
                        side=kind,
                        start_seconds=a["timestamp_seconds"],
                        end_seconds=b["timestamp_seconds"],
                        start_position=a["position"],
                        end_position=b["position"],
                    )
                    events.append(event)
                else:
                    event.update(end_seconds=b["timestamp_seconds"], end_position=b["position"])

        if len(segment) == 1:
            append_piece(
                side(segment[0]["normalized_semitones"]), vertex(segment[0]), vertex(segment[0])
            )
        for a, b in pairwise(segment):
            if (
                b["source_frame_index"] != a["source_frame_index"] + 1
                or not 0 < b["timestamp_seconds"] - a["timestamp_seconds"] <= 1.5 * cadence
            ):
                raise ValueError("caller must break missing/rejected evidence gaps")
            va, vb = a["normalized_semitones"], b["normalized_semitones"]
            fractions = [0.0, 1.0]
            if vb != va:
                fractions += [
                    (boundary - va) / (vb - va)
                    for boundary in domain
                    if 0 < (boundary - va) / (vb - va) < 1
                ]
            fractions.sort()

            def interpolate(fraction, a=a, b=b):
                return {k: a[k] + fraction * (b[k] - a[k]) for k in vertex(a)}

            for f0, f1 in pairwise(fractions):
                start, end = interpolate(f0), interpolate(f1)
                append_piece(side(va + (vb - va) * ((f0 + f1) / 2)), start, end)
            for f in fractions[1:-1]:
                crossings.append(
                    dict(
                        **interpolate(f),
                        segment_index=segment_index,
                        unit_key=unit["key"],
                        source_indices=[a["source_frame_index"], b["source_frame_index"]],
                    )
                )
        # Rails carry support duration, not fictitious measurements at a boundary.
        segment_events = [e for e in events if e["segment_index"] == segment_index]
        for e in segment_events:
            e["support_start_seconds"] = (
                support_start
                if e["start_seconds"] == segment[0]["timestamp_seconds"]
                else e["start_seconds"]
            )
            e["support_end_seconds"] = (
                support_end
                if e["end_seconds"] == segment[-1]["timestamp_seconds"]
                else e["end_seconds"]
            )
            e["duration_seconds"] = e["support_end_seconds"] - e["support_start_seconds"]
            rate = unit.get("display_position_per_second", 0)
            e["support_start_position"] = e["start_position"] + rate * (
                e["support_start_seconds"] - e["start_seconds"]
            )
            e["support_end_position"] = e["end_position"] + rate * (
                e["support_end_seconds"] - e["end_seconds"]
            )
            e["source_indices"] = [
                p["source_frame_index"]
                for p in segment
                if side(p["normalized_semitones"]) == e["side"]
                and e["start_seconds"] <= p["timestamp_seconds"] <= e["end_seconds"]
            ]
    count = sum(len(seg) for seg in segments)
    outside = sum(side(p["normalized_semitones"]) != "inside" for seg in segments for p in seg)
    duration = sum(e["duration_seconds"] for e in events)
    return dict(
        domain=domain,
        paths=paths,
        events=events,
        crossings=crossings,
        inside_points=count - outside,
        overflow_points=outside,
        overflow_point_fraction=outside / count if count else 0,
        overflow_duration_seconds=duration,
        selected_support_seconds=total_support,
        overflow_support_fraction=duration / total_support if total_support else 0,
    )

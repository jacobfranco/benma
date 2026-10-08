"""Research-only relative gestures within existing selected-evidence fragments.

Neither pitch magnitude nor linguistic identity can create a fragment boundary.
Accepted timing still owns one unit; fragments do not create finer timing claims.
"""

from __future__ import annotations

import math
import statistics
from typing import Any

from benchmark.pronunciation_v2.relative_pitch_gesture import Sample, Unit, project_relative


def relative_pitch_fragments(
    samples: list[Sample], units: list[Unit], *, cadence_seconds: float
) -> dict[str, Any]:
    """Intersect maximal selected runs with accepted units, then translate each.

    Use existing eligibility-run cadence semantics (<=1.5 * hop), and require
    consecutive original source indices. Rejected/missing frames always split,
    even a single missing frame. The half-hop tolerance handles time quantization;
    it is not a silence threshold. No frequency-derived split or interpolation.
    """
    if not math.isfinite(cadence_seconds) or cadence_seconds <= 0:
        raise ValueError("known positive extraction cadence required")
    # Reuse the prior prototype's validated timing/ownership and absolute values.
    # Its 45 ms segment guard is looser than 1.5*hop for this 10 ms tracker.
    # Restrict the prototype to that proven cadence regime, rather than silently
    # inheriting a tighter arbitrary break for some future different tracker.
    if 1.5 * cadence_seconds > 0.045:
        raise ValueError("prototype requires cadence <=30 ms")
    owned = project_relative(samples, units)
    selected_by_index = {s.source_index: s.selected_hz for s in samples}
    output_units, all_segments = [], []
    for unit in owned["units"]:
        absolute_runs = []
        for segment in unit["segments"]:
            current = []
            for point in segment:
                if current and (
                    point["source_frame_index"] != current[-1]["source_frame_index"] + 1
                    or point["timestamp_seconds"] - current[-1]["timestamp_seconds"]
                    > 1.5 * cadence_seconds
                ):
                    absolute_runs.append(current)
                    current = []
                current.append(point)
            if current:
                absolute_runs.append(current)
        fragments, segments = [], []
        for i, run in enumerate(absolute_runs):
            values = [p["absolute_semitones"] for p in run]
            center = statistics.median(values)
            key = f"{unit['key']}:{i}"
            points = [
                dict(p, normalized_semitones=p["absolute_semitones"] - center, fragment_key=key)
                for p in run
            ]
            first, last = points[0], points[-1]
            following = absolute_runs[i + 1][0] if i + 1 < len(absolute_runs) else None
            gap = None
            if following:
                elapsed = following["timestamp_seconds"] - last["timestamp_seconds"]
                gap = dict(
                    start_seconds=last["timestamp_seconds"],
                    end_seconds=following["timestamp_seconds"],
                    elapsed_between_selected_seconds=elapsed,
                    missing_support_seconds=max(0, elapsed - cadence_seconds),
                    intervening_source_frames=following["source_frame_index"]
                    - last["source_frame_index"]
                    - 1,
                )
            relative = [p["normalized_semitones"] for p in points]
            fragments.append(
                dict(
                    key=key,
                    unit_key=unit["key"],
                    selected_count=len(points),
                    source_indices=[p["source_frame_index"] for p in points],
                    start_seconds=first["timestamp_seconds"],
                    end_seconds=last["timestamp_seconds"],
                    endpoint_duration_seconds=last["timestamp_seconds"]
                    - first["timestamp_seconds"],
                    support_duration_seconds=last["timestamp_seconds"]
                    - first["timestamp_seconds"]
                    + cadence_seconds,
                    absolute_hz_range=[
                        min(selected_by_index[p["source_frame_index"]] for p in run),
                        max(selected_by_index[p["source_frame_index"]] for p in run),
                    ],
                    absolute_semitone_range=[min(values), max(values)],
                    center_semitones_re_1hz=center,
                    center_hz=2 ** (center / 12),
                    relative_range=[min(relative), max(relative)],
                    excursion_semitones=max(values) - min(values),
                    following_gap=gap,
                    segments=[points],
                )
            )
            segments.append(points)
        points = [p for seg in segments for p in seg]
        relative = [p["normalized_semitones"] for p in points]
        absolute = [p["absolute_semitones"] for p in points]
        output_units.append(
            dict(
                key=unit["key"],
                start_seconds=unit["start_seconds"],
                end_seconds=unit["end_seconds"],
                timing_source=unit["timing_source"],
                selected_count=len(points),
                fragment_count=len(fragments),
                fragments=fragments,
                segments=segments,
                absolute_semitone_range=[min(absolute), max(absolute)] if absolute else None,
                relative_range=[min(relative), max(relative)] if relative else None,
                whole_unit_center_semitones_re_1hz=unit["center_semitones_re_1hz"],
            )
        )
        all_segments.extend(segments)
    relative = [p["normalized_semitones"] for seg in all_segments for p in seg]
    return dict(
        units=output_units,
        segments=all_segments,
        minimum_semitones=min(-3, min(relative, default=0) - 1),
        maximum_semitones=max(3, max(relative, default=0) + 1),
        cadence_seconds=cadence_seconds,
        maximum_contiguous_step_seconds=1.5 * cadence_seconds,
        method="research-relative-pitch-fragments-v1",
    )


def fragment_pairwise_error(projected: dict[str, Any]) -> float:
    return max(
        (
            abs(
                (b["normalized_semitones"] - a["normalized_semitones"])
                - (b["absolute_semitones"] - a["absolute_semitones"])
            )
            for seg in projected["segments"]
            for a in seg
            for b in seg
        ),
        default=0.0,
    )

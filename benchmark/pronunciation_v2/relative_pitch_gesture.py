"""Research-only constant translation of selected measurements; no acoustic policy.

Inputs deliberately cannot carry characters, targets, tones, or candidate choices.
The caller supplies already accepted timing. No timing means no projected points.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Sample:
    source_index: int
    timestamp_seconds: float
    selected_hz: float | None


@dataclass(frozen=True)
class Unit:
    key: str
    start: float
    end: float
    timing_source: str


def project_relative(samples: list[Sample], units: list[Unit]) -> dict[str, Any]:
    """Keep full-resolution selected geometry, subtract one median per unit.

    Half-open ownership matches mobile (later start, then later unit wins tiny
    overlaps). Null evidence, source-index discontinuity, and >45 ms gaps split
    lines. Independent units always have separate segments. No rounding/smoothing.
    """
    if len({u.key for u in units}) != len(units):
        raise ValueError("duplicate unit key")
    for u in units:
        if not (math.isfinite(u.start) and math.isfinite(u.end) and 0 <= u.start < u.end):
            raise ValueError("invalid accepted timing")
        if not u.timing_source or u.timing_source in {
            "synthetic",
            "equal_split",
            "synthetic_replay",
        }:
            raise ValueError("untrusted timing")
    for i, s in enumerate(samples):
        if not math.isfinite(s.timestamp_seconds) or s.timestamp_seconds < 0:
            raise ValueError("invalid sample time")
        if i and (
            s.source_index <= samples[i - 1].source_index
            or s.timestamp_seconds <= samples[i - 1].timestamp_seconds
        ):
            raise ValueError("samples must retain strict source order")
        if s.selected_hz is not None and not (math.isfinite(s.selected_hz) and s.selected_hz > 0):
            raise ValueError("invalid selected frequency; projection cannot reject it")
    ownership = [
        max(
            (i for i, u in enumerate(units) if u.start <= s.timestamp_seconds < u.end),
            key=lambda i: (units[i].start, i),
            default=None,
        )
        for s in samples
    ]
    rows, segments = [], []
    for owner, unit in enumerate(units):
        selected = [
            s
            for s, o in zip(samples, ownership, strict=True)
            if o == owner and s.selected_hz is not None
        ]
        hz_values = [s.selected_hz for s in selected if s.selected_hz is not None]
        values = [12 * math.log2(hz) for hz in hz_values]  # reference = 1 Hz
        center = statistics.median(values) if values else None
        local: list[list[dict[str, Any]]] = []
        current: list[dict[str, Any]] = []
        for s, value in zip(selected, values, strict=True):
            assert center is not None
            if current and (
                s.source_index != current[-1]["source_frame_index"] + 1
                or s.timestamp_seconds - current[-1]["timestamp_seconds"] > 0.045
            ):
                local.append(current)
                current = []
            current.append(
                dict(
                    source_frame_index=s.source_index,
                    timestamp_seconds=s.timestamp_seconds,
                    absolute_semitones=value,
                    normalized_semitones=value - center,
                    unit_key=unit.key,
                )
            )
        if current:
            local.append(current)
        relative = [p["normalized_semitones"] for seg in local for p in seg]
        rows.append(
            dict(
                key=unit.key,
                start_seconds=unit.start,
                end_seconds=unit.end,
                timing_source=unit.timing_source,
                selected_count=len(selected),
                center_semitones_re_1hz=center,
                center_hz=2 ** (center / 12) if center is not None else None,
                hz_range=[
                    min(hz_values),
                    max(hz_values),
                ]
                if selected
                else None,
                relative_range=[min(relative), max(relative)] if relative else None,
                five_bin_relative_medians=[
                    statistics.median(
                        relative[i * len(relative) // 5 : (i + 1) * len(relative) // 5]
                    )
                    for i in range(5)
                ]
                if len(relative) >= 5
                else None,
                segments=local,
            )
        )
        segments.extend(local)
    values = [p["normalized_semitones"] for seg in segments for p in seg]
    return dict(
        units=rows,
        segments=segments,
        minimum_semitones=min(-3, min(values, default=0) - 1),
        maximum_semitones=max(3, max(values, default=0) + 1),
        method="research-relative-measured-gesture-median-v1",
    )


def pairwise_error(projected: dict[str, Any]) -> float:
    """Exhaust all pairs, including pairs across a gap within the same unit."""
    return max(
        (
            abs(
                (b["normalized_semitones"] - a["normalized_semitones"])
                - (b["absolute_semitones"] - a["absolute_semitones"])
            )
            for unit in projected["units"]
            for a in [p for seg in unit["segments"] for p in seg]
            for b in [p for seg in unit["segments"] for p in seg]
        ),
        default=0.0,
    )

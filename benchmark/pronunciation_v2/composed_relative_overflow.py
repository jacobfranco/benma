"""Bounded research composition; selected evidence and accepted units are inputs.

One median per accepted timing unit, one linear shared robust relative window.
Existing gap structure and mobile X coordinates are preserved verbatim.
"""

from __future__ import annotations

import math
import statistics

from benchmark.pronunciation_v2.robust_domain_overflow import project_with_overflow

POLICIES = {"mad2.5": 2.5, "mad3": 3.0, "mad3.5": 3.5}


def center_timing_units(segments, units):
    """Translate full selected measurements; never split/merge input segments."""
    keys = {u["key"] for u in units}
    if len(keys) != len(units):
        raise ValueError("duplicate accepted unit")
    for segment in segments:
        if not segment or len({p["unit_key"] for p in segment}) != 1:
            raise ValueError("independent timing units require separate segments")
        if segment[0]["unit_key"] not in keys:
            raise ValueError("selected evidence requires accepted timing")
    centers, rows = {}, []
    for unit in units:
        points = [p for s in segments for p in s if p["unit_key"] == unit["key"]]
        values = []
        for p in points:
            hz = p["selected_f0_hz"]
            if not math.isfinite(hz) or hz <= 0:
                raise ValueError("invalid selected Hz; cannot silently reject")
            if not unit["start_seconds"] <= p["timestamp_seconds"] < unit["end_seconds"]:
                raise ValueError("sample outside its accepted timing")
            values.append(12 * math.log2(hz))
        center = statistics.median(values) if values else None
        centers[unit["key"]] = center
        rows.append(
            unit
            | dict(
                selected_count=len(points),
                center_semitones_re_1hz=center,
                center_hz=2 ** (center / 12) if center is not None else None,
                relative_range=[min(values) - center, max(values) - center] if values else None,
                excursion_semitones=max(values) - min(values) if values else None,
            )
        )
    result = [
        [
            p
            | dict(
                absolute_semitones=12 * math.log2(p["selected_f0_hz"]),
                normalized_semitones=12 * math.log2(p["selected_f0_hz"]) - centers[p["unit_key"]],
            )
            for p in s
        ]
        for s in segments
    ]
    return result, rows


def relative_domain(segments, multiplier=None):
    """Full range or normal-consistent MAD, bounded before ±1 st padding.

    Match prior strongest prototype: 1.4826 * raw MAD, minimum [-3,+3].
    The multiplier is deliberately limited to the three predeclared candidates.
    """
    if multiplier is not None and multiplier not in POLICIES.values():
        raise ValueError("outside bounded comparison")
    values = [p["normalized_semitones"] for s in segments for p in s]
    if not values:
        return [-3.0, 3.0]
    low, high = min(values), max(values)
    if multiplier is not None:
        center = statistics.median(values)
        spread = 1.4826 * statistics.median(abs(v - center) for v in values)
        low, high = max(low, center - multiplier * spread), min(high, center + multiplier * spread)
    return [min(-3.0, low - 1), max(3.0, high + 1)]


def compose(segments, units, cadence):
    relative, centers = center_timing_units(segments, units)
    policies = {}
    for policy, multiplier in POLICIES.items():
        domain = relative_domain(relative, multiplier)
        projected = project_with_overflow(relative, domain, units, cadence)
        projected["units"] = []
        for unit in centers:
            local = project_with_overflow(
                [s for s in relative if s[0]["unit_key"] == unit["key"]], domain, units, cadence
            )
            projected["units"].append(
                {**unit, **{k: v for k, v in local.items() if k not in {"paths", "crossings"}}}
            )
        projected["affected_units"] = [
            u["label"] for u in projected["units"] if u["overflow_points"]
        ]
        projected["entirely_outside_units"] = [
            u["label"]
            for u in projected["units"]
            if u["overflow_points"] and not u["inside_points"]
        ]
        policies[policy] = projected
    return dict(
        segments=relative,
        units=centers,
        centered_domain=relative_domain(relative),
        policies=policies,
    )

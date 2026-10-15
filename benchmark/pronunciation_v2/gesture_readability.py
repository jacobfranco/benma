"""Research-only geometry of retained graph measurements, never a tone classifier.

No production imports this module. Thresholds are a fixed candidate policy, not
calibrated pronunciation criteria. No text, expected tones, or raw Hz are inputs.
"""

from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass, field
from itertools import pairwise
from typing import Any, Literal

Gesture = Literal["level", "rising", "falling", "dip_rise", "unclear"]
Readability = Literal["readable", "tentative", "unavailable"]


@dataclass(frozen=True)
class Point:
    index: int
    t: float
    st: float


@dataclass(frozen=True)
class Result:
    gesture: Gesture = "unclear"
    readability: Readability = "unavailable"
    reason: str = "insufficient_support"
    features: dict[str, float] = field(default_factory=dict)
    perturbations: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _geometry(segments: list[list[Point]], hop: float) -> Result:
    points = [p for s in segments for p in s]
    if len(points) < 12 or len(points) * hop < 0.12 - 1e-8:
        return Result()
    extent = points[-1].t - points[0].t + hop
    gaps = [b.t - a.t - hop for a, b in pairwise(points) if b.t - a.t > hop * 1.5]
    jumps = [abs(b.st - a.st) for a, b in pairwise(points)]
    # Three actual neighboring samples, entirely within one retained segment.
    # This summarizes the graph; it neither replaces nor interpolates its points.
    smooth = [
        Point(s[i].index, s[i].t, statistics.median(p.st for p in s[i - 1 : i + 2]))
        for s in segments
        for i in range(1, len(s) - 1)
        if s[i].t - s[i - 1].t <= hop * 1.5 and s[i + 1].t - s[i].t <= hop * 1.5
    ]
    if len(smooth) < 8:
        return Result()
    first, last = (
        statistics.median(p.st for p in points[:3]),
        statistics.median(p.st for p in points[-3:]),
    )
    low, high = min(p.st for p in smooth), max(p.st for p in smooth)
    # A shallow wobble on a low plateau must not move the turning region to the
    # first near-equal minimum. Keep real low-region timestamps, not a fitted U.
    low_times = [p.t for p in smooth if p.st <= low + 0.5]
    minimum_time = statistics.median(low_times)
    minimum_position = (minimum_time - points[0].t) / max(hop, extent - hop)
    features = {
        "start_st": first,
        "end_st": last,
        "minimum_st": low,
        "maximum_st": high,
        "minimum_time": minimum_time,
        "minimum_position": minimum_position,
        "fall_st": first - low,
        "recovery_st": last - low,
        "net_st": last - first,
        "excursion_st": high - low,
        "support_seconds": len(points) * hop,
        "support_fraction": len(points) * hop / extent,
        "gap_count": float(len(gaps)),
        "largest_gap_seconds": max(gaps, default=0),
        "maximum_selected_jump_st": max(jumps, default=0),
        "selected_discontinuities": float(sum(x > 6 for x in jumps)),
    }
    if max(gaps, default=0) > 0.08 + 1e-8 or features["support_fraction"] < 0.8:
        return Result(reason="missing_critical_support", features=features)
    if max(jumps, default=0) > 6:
        return Result(reason="contradictory_selected_fragments", features=features)
    # Direction consistency never counts a movement across a missing interval.
    steps = [(a, b, b.st - a.st) for a, b in pairwise(smooth) if b.t - a.t <= hop * 1.5]

    def consistency(direction: int, start: float, end: float) -> float:
        moves = [v for a, b, v in steps if a.t >= start and b.t <= end]
        total = sum(abs(v) for v in moves)
        return sum(max(0, direction * v) for v in moves) / total if total else 0

    fall = consistency(-1, points[0].t, minimum_time)
    rise = consistency(1, minimum_time, points[-1].t)
    features.update(fall_consistency=fall, rise_consistency=rise)
    label: Gesture = "unclear"
    if (
        0.15 <= minimum_position <= 0.85
        and first - low >= 1.5
        and last - low >= 1.5
        and fall >= 0.7
        and rise >= 0.7
    ):
        label = "dip_rise"
    elif high - low <= 1.5 and abs(last - first) <= 1:
        label = "level"
    elif (
        last - first >= 2 and first - low < 1.5 and consistency(1, points[0].t, points[-1].t) >= 0.8
    ):
        label = "rising"
    elif (
        last - first <= -2
        and last - low < 1.5
        and consistency(-1, points[0].t, points[-1].t) >= 0.8
    ):
        label = "falling"
    return Result(
        label,
        "readable" if label != "unclear" else "unavailable",
        "retained_geometry" if label != "unclear" else "ambiguous_geometry",
        features,
    )


def summarize(
    segments: list[list[Point]],
    *,
    integrity: str = "sufficient",
    grouped: bool = False,
    flagged_indices: tuple[int, ...] = (),
    hop: float = 0.01,
) -> Result:
    if grouped:
        return Result(reason="grouped_evidence")
    base = _geometry(segments, hop)
    if base.gesture == "unclear":
        return base
    points = [p for s in segments for p in s]
    removals = {
        "first_frame": {points[0].index},
        "last_frame": {points[-1].index},
        "sparse_tenth": {p.index for p in points[9::10]},
        "flagged_discontinuities": set(flagged_indices),
    }
    checks: dict[str, str] = {}
    for name, removed in removals.items():
        # Preserve every original gap. Deleted points introduce missing support;
        # no synthesized value or line is inserted in the original graph.
        perturbed = [[p for p in s if p.index not in removed] for s in segments]
        perturbed = [s for s in perturbed if s]
        checks[name] = _geometry(perturbed, hop).gesture
    if any(label != base.gesture for label in checks.values()):
        return Result(reason="perturbation_sensitive", features=base.features, perturbations=checks)
    state: Readability = "readable" if integrity == "sufficient" else "tentative"
    return Result(
        base.gesture,
        state,
        "retained_geometry_only" if state == "tentative" else base.reason,
        base.features,
        checks,
    )


def main() -> None:
    import csv
    import json
    from collections import Counter
    from pathlib import Path

    folder = (
        Path(__file__).resolve().parents[2]
        / "docs/research/pronunciation-v2/2026-10-08-gesture-readability"
    )
    corpus_path = folder / "calibration-corpus.json"
    rows = json.loads(corpus_path.read_text())
    results = []
    for row in rows:
        result = summarize(
            [[Point(**p) for p in s] for s in row["segments"]],
            integrity=row["eligibility"]["state"],
            grouped=row["grouped"],
            flagged_indices=tuple(row["flagged_indices"]),
        )
        results.append({**row, "proposed": result.as_dict()})
    (folder / "calibration-results.json").write_text(
        json.dumps(results, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    with (folder / "calibration-comparison.csv").open("w") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            [
                "unit",
                "strict_integrity",
                "current_gesture",
                "current_reason",
                "five_bins_st",
                "proposed_gesture",
                "readability",
                "manual_geometry",
                "comparison",
                "reason",
                "start_st",
                "minimum_st",
                "end_st",
                "minimum_position",
                "fall_st",
                "recovery_st",
                "support_seconds",
                "largest_gap_seconds",
                "maximum_selected_jump_st",
                "perturbations",
            ]
        )
        for row in results:
            result = row["proposed"]
            comparison = (
                "abstained"
                if result["gesture"] == "unclear"
                else "agrees"
                if result["gesture"].upper() == row["manual_geometry"]
                else "disagrees"
            )
            writer.writerow(
                [
                    row["id"],
                    row["eligibility"]["state"],
                    row["current_gesture"],
                    row["current_reason"],
                    [row["current_features"].get(f"bin_{i}_st") for i in range(1, 6)],
                    result["gesture"],
                    result["readability"],
                    row["manual_geometry"],
                    comparison,
                    result["reason"],
                    *[
                        result["features"].get(k)
                        for k in (
                            "start_st",
                            "minimum_st",
                            "end_st",
                            "minimum_position",
                            "fall_st",
                            "recovery_st",
                            "support_seconds",
                            "largest_gap_seconds",
                            "maximum_selected_jump_st",
                        )
                    ],
                    json.dumps(result["perturbations"], sort_keys=True),
                ]
            )

    def old_label(row: dict[str, Any]) -> str:
        current = str(row["current_gesture"])
        return {"dipping": "DIP_RISE"}.get(current, current.upper())

    summary = {
        "items": len(rows),
        "manual_geometry_counts": dict(Counter(r["manual_geometry"] for r in rows)),
        "current_named": sum(r["current_gesture"] != "unclear" for r in rows),
        "current_agrees_named": sum(
            old_label(r) == r["manual_geometry"] != "UNCLEAR" for r in rows
        ),
        "proposed_named": sum(r["proposed"]["gesture"] != "unclear" for r in results),
        "proposed_agrees_named": sum(
            r["proposed"]["gesture"].upper() == r["manual_geometry"] != "UNCLEAR" for r in results
        ),
        "new_useful_descriptions": [
            r["id"]
            for r in results
            if r["proposed"]["gesture"].upper() == r["manual_geometry"] != "UNCLEAR"
            and old_label(r) != r["manual_geometry"]
        ],
        "lost_current_agreements": [
            r["id"]
            for r in results
            if old_label(r) == r["manual_geometry"] != "UNCLEAR"
            and r["proposed"]["gesture"].upper() != r["manual_geometry"]
        ],
        "mixed_described": [
            r["id"] for r in results if r["proposed"]["readability"] == "tentative"
        ],
        "perturbation_sensitive": [
            r["id"] for r in results if r["proposed"]["reason"] == "perturbation_sensitive"
        ],
        "annotation_limit": (
            "Assistant numeric review, not independent human listening/visual certification; "
            "current dipping mapped to DIP_RISE for this coarse comparison only."
        ),
    }
    (folder / "calibration-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

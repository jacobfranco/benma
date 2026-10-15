"""Frozen geometry comparison. Run from repository root; no new audio or provider calls.

Uses the actual mobile shape/display model via the adjacent Node bridge. Linear and
quadratic alternatives are numeric research comparators, never production classifiers.
"""

from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/research/pronunciation-v2/2026-10-09-product-feedback"
CORPUS = (
    ROOT / "docs/research/pronunciation-v2/2026-10-08-gesture-readability/calibration-corpus.json"
)


def candidates(row: dict) -> dict:
    points = [p for segment in row["segments"] for p in segment]
    if len(points) < 8:
        return {"linear": "UNCLEAR", "quadratic": "UNCLEAR"}
    x = np.array([(p["t"] - row["start"]) / (row["end"] - row["start"]) for p in points])
    y = np.array([p["st"] for p in points])
    y -= np.median(y)
    slopes = [
        (y[j] - y[i]) / (x[j] - x[i])
        for i in range(len(x))
        for j in range(i + 1, len(x))
        if x[j] > x[i]
    ]
    slope = float(np.median(slopes))
    intercept = float(np.median(y - slope * x))
    excursion = slope * (x[-1] - x[0])
    residual = float(np.median(abs(y - (slope * x + intercept))))
    linear = (
        (
            "RISING"
            if excursion >= 1.5
            else "FALLING"
            if excursion <= -1.5
            else "LEVEL"
            if np.ptp(y) <= 1.5
            else "UNCLEAR"
        )
        if residual <= 0.75
        else "UNCLEAR"
    )
    # Iteratively downweight residual outliers; fit only at actual observed times.
    weights = np.ones(len(x))
    coef = np.zeros(3)
    for _ in range(4):
        coef = np.polyfit(x, y, 2, w=np.sqrt(weights))
        errors = abs(y - np.polyval(coef, x))
        scale = max(0.1, float(np.median(errors)) * 1.4826)
        weights = np.minimum(1, 1.345 * scale / np.maximum(errors, 1e-9))
    a, b, _ = coef
    minimum = float(-b / (2 * a)) if abs(a) > 1e-9 else -1
    pos = (minimum - x[0]) / (x[-1] - x[0])
    low = float(np.polyval(coef, minimum))
    fall = float(np.polyval(coef, x[0])) - low
    rise = float(np.polyval(coef, x[-1])) - low
    quadratic_residual = float(np.median(abs(y - np.polyval(coef, x))))
    quadratic = (
        "DIP_RISE"
        if a > 0 and 0.1 <= pos <= 0.9 and min(fall, rise) >= 1 and quadratic_residual <= 0.75
        else linear
    )
    return {
        "linear": linear,
        "linear_slope_st_per_span": slope,
        "linear_residual_st": residual,
        "quadratic": quadratic,
        "quadratic_coefficients": coef.tolist(),
        "quadratic_minimum_position": pos,
        "quadratic_fall_st": fall,
        "quadratic_recovery_st": rise,
        "quadratic_residual_st": quadratic_residual,
    }


def guarded_candidates(row: dict) -> dict:
    points = [p for segment in row["segments"] for p in segment]
    if row["grouped"] or len(points) < 8:
        return {"linear": "UNCLEAR", "quadratic": "UNCLEAR"}
    t = np.array([p["t"] for p in points])
    y = np.array([p["st"] for p in points])
    dt = np.diff(t)
    if (
        t[-1] - t[0] < 0.07 - 1e-8
        or any(dt <= 0)
        or max(dt) > 0.09 + 1e-8
        or len(points) * 0.01 / (t[-1] - t[0] + 0.01) < 0.75
        or max(abs(np.diff(y))) > 6
        or any((dt > 0.025 + 1e-8) & (abs(np.diff(y)) > 1.5))
    ):
        return {"linear": "UNCLEAR", "quadratic": "UNCLEAR"}
    return candidates(row)


def stable_candidates(row: dict) -> dict:
    base = guarded_candidates(row)
    points = [p for segment in row["segments"] for p in segment]
    if not points:
        return base
    removals = [
        [points[0]["index"]],
        [points[-1]["index"]],
        [p["index"] for p in points[9::10]],
        row["flagged_indices"],
    ]
    variants = [
        guarded_candidates(
            {
                **row,
                "segments": [
                    [p for p in segment if p["index"] not in removed] for segment in row["segments"]
                ],
            }
        )
        for removed in removals
    ]
    return {
        **base,
        **{
            name: base[name] if all(v[name] == base[name] for v in variants) else "UNCLEAR"
            for name in ["linear", "quadratic"]
        },
    }


def expected(s: dict) -> str:
    if (
        s.get("reading_source") == "unresolved"
        or not s.get("pinyin")
        or s.get("expected_surface_tone") is None
    ):
        return "CONTEXT_UNRESOLVED"
    return {0: "FLEXIBLE_NEUTRAL", 1: "LEVEL", 2: "RISING", 3: "LOW_OR_DIP", 4: "FALLING"}[
        s["expected_surface_tone"]
    ]


def comparison(shape: dict, exp: str, grouped: bool) -> tuple[str, str]:
    """Research proposal only: never maps production colors or grades."""
    observed = shape["shape"]
    f = shape["features"]
    if grouped or observed == "UNCLEAR" or exp == "CONTEXT_UNRESOLVED":
        return "UNAVAILABLE", "unresolved_shape_context_or_group"
    if exp == "FLEXIBLE_NEUTRAL":
        return "UNAVAILABLE", "neutral_has_no_constrained_shape"
    if exp == "LOW_OR_DIP":
        if observed == "DIP_RISE":
            return "PARTIAL_OR_WEAK", "compatible_dip_but_low_register_and_context_not_established"
        return "UNAVAILABLE", "shape_alone_cannot_establish_low_register"
    if observed == exp:
        strength = abs(f.get("net_st", 0)) if observed != "LEVEL" else 3
        return ("STRONG_MATCH" if strength >= 2 else "PARTIAL_OR_WEAK"), "direction_agreement_only"
    if (exp, observed) in [("RISING", "FALLING"), ("FALLING", "RISING")]:
        return "CLEAR_DIFFERENCE", "opposite_coherent_directions"
    return "UNAVAILABLE", "deviation_needs_context_validation"


def run() -> None:
    rows = json.loads(CORPUS.read_text())
    actual = json.loads(
        subprocess.check_output(
            ["node", str(ROOT / "benchmark/pronunciation_v2/product_feedback.cjs")],
            input=CORPUS.read_bytes(),
        )
    )
    # Frozen derived context makes the audit reproducible without private audio/DB.
    context = json.loads((OUT / "expected-context.json").read_text())["units"]
    results = []
    for row, projected in zip(rows, actual, strict=True):
        member = context[row["id"]]
        exp = expected(member)
        proposed, reason = comparison(projected["result"], exp, row["grouped"])
        old = "DIP_RISE" if row["current_gesture"] == "dipping" else row["current_gesture"].upper()
        item = {
            **row,
            "previous_shape": old,
            "retained_count": sum(map(len, row["segments"])),
            "raw_selected_excursion_st": (
                float(np.ptp([p["st"] for segment in row["segments"] for p in segment]))
                if any(row["segments"])
                else None
            ),
            "acceptance": "SAVED_PRESENCE_ACCEPT_LANGUAGE_UNTESTED",
            "normalized_display": projected["display"],
            "shape": projected["result"],
            "alternatives": stable_candidates(row),
            "ungated_fits": candidates(row),
            "expected_shape": exp,
            "surface_rule": member.get("surface_rule"),
            "proposed_learner_state": proposed,
            "comparison_reason": reason,
            "human_visible_review": (
                "Assistant inspected retained numeric contour plots; "
                "frozen manual label unchanged. "
                "Not independent human validation."
            ),
        }
        results.append(item)
    summary = {
        "items": len(rows),
        "retained_points": sum(r["retained_count"] for r in results),
        "results": {},
    }
    for name, labels in [
        ("previous", [r["previous_shape"] for r in results]),
        ("linear", [r["alternatives"]["linear"] for r in results]),
        ("quadratic", [r["alternatives"]["quadratic"] for r in results]),
        ("piecewise", [r["shape"]["shape"] for r in results]),
    ]:
        summary["results"][name] = {
            "counts": dict(Counter(labels)),
            "agrees_unambiguous": sum(
                label == row["manual_geometry"] != "UNCLEAR"
                for row, label in zip(rows, labels, strict=True)
            ),
            "named_on_unclear_review": [
                r["id"]
                for r, label in zip(rows, labels, strict=True)
                if label != "UNCLEAR" and r["manual_geometry"] == "UNCLEAR"
            ],
        }
    summary["lost_previous_useful"] = [
        r["id"]
        for r in results
        if r["previous_shape"] == r["manual_geometry"] != "UNCLEAR"
        and r["shape"]["shape"] != r["manual_geometry"]
    ]
    summary["new_useful"] = [
        r["id"]
        for r in results
        if r["previous_shape"] != r["manual_geometry"]
        and r["shape"]["shape"] == r["manual_geometry"] != "UNCLEAR"
    ]
    summary["unstable"] = [
        r["id"] for r in results if r["shape"]["reason"] == "perturbation_sensitive"
    ]
    summary["proposed_comparison"] = dict(Counter(r["proposed_learner_state"] for r in results))
    summary["scale_floor_comparison"] = {
        str(floor): {
            "maximum_0_2_st_height_fraction": 0.2 / floor,
            "median_selected_range_fraction": float(
                np.median(
                    [
                        min(
                            1,
                            (
                                max(p["st"] for s in r["segments"] for p in s)
                                - min(p["st"] for s in r["segments"] for p in s)
                            )
                            / floor,
                        )
                        for r in rows
                        if r["segments"]
                    ]
                )
            ),
        }
        for floor in (4, 6, 8)
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "shape-results.json").write_text(
        json.dumps(results, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    (OUT / "shape-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    fields = [
        "id",
        "acceptance",
        "retained_count",
        "observed_shape",
        "raw_selected_excursion_st",
        "shape_reason",
        "stability",
        "expected_shape",
        "proposed_learner_state",
        "previous_shape",
        "manual_geometry",
        "linear",
        "quadratic",
        "review",
    ]
    with (OUT / "calibration-matrix.csv").open("w") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow(
                {k: r[k] for k in fields if k in r}
                | {
                    "observed_shape": r["shape"]["shape"],
                    "shape_reason": r["shape"]["reason"],
                    "stability": json.dumps(r["shape"]["perturbations"]),
                    "linear": r["alternatives"]["linear"],
                    "quadratic": r["alternatives"]["quadratic"],
                    "review": r["manual_reason"],
                }
            )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run()

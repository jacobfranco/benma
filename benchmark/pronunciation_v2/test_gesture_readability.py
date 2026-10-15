from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from benchmark.pronunciation_v2.gesture_readability import Point, summarize


def contour(values):
    return [[Point(i, i / 100, v) for i, v in enumerate(values)]]


U_ABOVE = [4 - i * 0.2 for i in range(31)] + [-2 + i * 0.25 for i in range(1, 41)]
U_BELOW = [5 - i * 0.2 for i in range(31)] + [-1 + i * 0.125 for i in range(1, 41)]


@pytest.mark.parametrize(
    "values,label",
    [
        (U_ABOVE, "dip_rise"),
        (U_BELOW, "dip_rise"),
        ([i * 0.1 for i in range(60)], "rising"),
        ([-i * 0.1 for i in range(60)], "falling"),
        ([0.1 * (i % 3) for i in range(60)], "level"),
        ([i / 200 for i in range(60)], "level"),
    ],
)
def test_coarse_numeric_geometry_and_sensitivity(values, label):
    segments = contour(values)
    before = copy.deepcopy(segments)
    r = summarize(segments)
    assert r.gesture == label and r.readability == "readable"
    assert set(r.perturbations.values()) == {label}
    assert segments == before
    assert summarize(contour([v + 12 for v in values])).gesture == label


@pytest.mark.parametrize("start,end", [(12, 14), (47, 49)])
def test_small_gaps_before_or_after_minimum_remain_missing(start, end):
    points = contour(U_ABOVE)[0]
    segments = [points[:start], points[end:]]
    r = summarize(segments)
    assert r.gesture == "dip_rise"
    assert r.features["gap_count"] == 1
    assert r.features["largest_gap_seconds"] == pytest.approx(0.02)
    assert sum(len(s) for s in segments) == len(points) - 2


def test_missing_turning_region_does_not_invent_a_valley():
    points = contour(U_ABOVE)[0]
    r = summarize([points[:20], points[42:]])
    assert r.gesture == "unclear" and r.reason == "missing_critical_support"


def test_endpoint_minimum_is_not_a_supported_dip_rise():
    r = summarize(contour([3 - i * 0.5 for i in range(7)] + [i * 0.1 for i in range(1, 54)]))
    assert r.gesture == "unclear"


@pytest.mark.parametrize(
    "segments",
    [
        contour([*U_ABOVE[:20], 16, *U_ABOVE[21:]]),
        [
            contour([3 - i * 0.1 for i in range(25)])[0],
            [Point(30 + i, 0.3 + i / 100, 12 + i * 0.1) for i in range(25)],
        ],
    ],
)
def test_discontinuity_or_incompatible_fragments_cannot_become_readable(segments):
    r = summarize(segments)
    assert r.gesture == "unclear" and r.readability == "unavailable"


def test_grouped_and_insufficient_evidence_abstain():
    assert summarize(contour(U_ABOVE), grouped=True).reason == "grouped_evidence"
    assert summarize([]).readability == "unavailable"
    assert summarize(contour([0] * 8)).readability == "unavailable"


def test_saved_exaggerated_units_are_stable_but_clean_edge_regression_is_retained():
    rows = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "docs/research/pronunciation-v2/2026-10-08-gesture-readability"
            / "calibration-corpus.json"
        ).read_text()
    )
    by_id = {r["id"]: r for r in rows}
    for text in "我想买":
        row = by_id[f"7e6b6fe9:{text}"]
        before = copy.deepcopy(row)
        r = summarize(
            [[Point(**p) for p in s] for s in row["segments"]],
            integrity=row["eligibility"]["state"],
            flagged_indices=tuple(row["flagged_indices"]),
        )
        assert r.gesture == "dip_rise"
        assert r.readability == ("readable" if text == "我" else "tentative")
        assert row == before
    edge = by_id["0b194cf9:我"]
    r = summarize([[Point(**p) for p in s] for s in edge["segments"]])
    assert r.reason == "perturbation_sensitive"
    assert r.perturbations["first_frame"] == "unclear"
    # The failing calibration case is not erased to make the release gate pass.


def test_flagged_points_that_change_geometry_prevent_readability():
    points = contour(U_ABOVE)
    r = summarize(points, integrity="unstable", flagged_indices=tuple(range(24, 36)))
    assert r.reason == "perturbation_sensitive"

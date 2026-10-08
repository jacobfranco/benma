"""Display-only invariants, analytical crossings, and physical acceptance limits."""

import copy
import hashlib
import json
import math
from itertools import pairwise
from pathlib import Path

import pytest

from benchmark.pronunciation_v2.robust_domain_overflow import (
    POLICIES,
    derive_mine_display_domain,
    project_with_overflow,
)
from benchmark.pronunciation_v2.robust_domain_overflow_report import control, measured_segments

REPORT = (
    Path(__file__).resolve().parents[2]
    / "docs/research/pronunciation-v2/2026-10-07-relative-pitch-gesture/overflow-replay.json"
)
UNITS = [dict(key="0", label="fixture", start_seconds=0, end_seconds=1)]


def segment(values, offset=0):
    return [
        dict(
            source_frame_index=i + offset,
            timestamp_seconds=(i + offset) * 0.01,
            position=(i + offset) * 0.1,
            normalized_semitones=v,
            unit_key="0",
        )
        for i, v in enumerate(values)
    ]


def project(values, domain=(-3, 3)):
    return project_with_overflow([segment(values)], list(domain), UNITS, 0.01)


def replay():
    return json.loads(REPORT.read_text())


def test_ordinary_segment_unchanged_and_linear_amplitude():
    p = project([-2, 0, 2])
    assert [q["normalized_semitones"] for q in p["paths"][0]] == [-2, 0, 2]
    assert not p["events"]

    def y(v):
        return 128 - (v + 3) / 6 * 128

    assert (y(0) - y(2)) / (y(-2) - y(2)) == pytest.approx(0.5)


@pytest.mark.parametrize("values,boundary,side", [([0, -6], -3, "below"), ([0, 6], 3, "above")])
def test_crossing_is_interpolated_in_time_and_x(values, boundary, side):
    p = project(values)
    assert p["crossings"][0]["timestamp_seconds"] == pytest.approx(0.005)
    assert p["crossings"][0]["position"] == pytest.approx(0.05)
    assert p["paths"][0][-1]["normalized_semitones"] == boundary
    assert p["events"][0]["side"] == side


def test_multi_frame_run_one_event_and_exact_reentry():
    p = project([0, 6, 7, 6, 0])
    assert len(p["events"]) == 1
    assert len(p["paths"]) == 2
    assert p["events"][0]["source_indices"] == [1, 2, 3]
    assert p["events"][0]["start_seconds"] == pytest.approx(0.005)
    assert p["events"][0]["end_seconds"] == pytest.approx(0.035)
    assert p["paths"][1][0]["position"] == pytest.approx(0.35)
    assert p["events"][0]["duration_seconds"] == pytest.approx(0.03)


def test_both_boundaries_crossed_in_one_segment():
    p = project([-6, 6])
    assert len(p["events"]) == 2
    assert [v["timestamp_seconds"] for v in p["crossings"]] == pytest.approx([0.0025, 0.0075])
    assert [v["normalized_semitones"] for v in p["paths"][0]] == [-3, 3]


def test_gap_never_connects_lines_or_overflow_rails():
    p = project_with_overflow([segment([0, 6]), segment([6, 0], 3)], [-3, 3], UNITS, 0.01)
    assert len(p["events"]) == 2
    assert p["events"][0]["support_end_seconds"] < p["events"][1]["support_start_seconds"]
    with pytest.raises(ValueError, match="gap"):
        project_with_overflow([segment([0, 6]) + segment([6, 0], 3)], [-3, 3], UNITS, 0.01)


def test_sustained_outside_run_keeps_240ms_support():
    p = project_with_overflow([segment([20] * 24, 10)], [-3, 3], UNITS, 0.01)
    assert len(p["events"]) == 1 and not p["paths"]
    assert p["events"][0]["duration_seconds"] == pytest.approx(0.24)
    assert p["events"][0]["end_position"] - p["events"][0]["start_position"] == pytest.approx(2.3)


def test_extreme_source_point_metadata_and_input_remain_identical():
    source = [segment([0, 1, -40, 2])]
    source[0][2].update(selected_f0_hz=54.61, retained=True, confidence=0.9)
    before = copy.deepcopy(source)
    p = project_with_overflow(source, [-3, 3], UNITS, 0.01)
    assert source == before
    assert p["events"][0]["source_indices"] == [2]


@pytest.mark.parametrize("policy", POLICIES)
def test_tiny_noise_preserves_six_st_minimum_window(policy):
    assert derive_mine_display_domain([segment([0, 0.5, 0])], policy) == [-3, 3]


@pytest.mark.parametrize("base", [54.61, 55, 60, 70, 350, 380, 440])
def test_same_coherent_shape_in_every_absolute_register(base):
    a = control("control", [base * 2 ** (v / 12) for v in [2, 1, 0, 1, 2]])
    b = control("control", [100 * 2 ** (v / 12) for v in [2, 1, 0, 1, 2]])
    for policy in POLICIES:
        assert a["policies"][policy]["domain"] == pytest.approx(b["policies"][policy]["domain"])
        assert not a["policies"][policy]["events"]


def test_no_accepted_timing_cannot_create_mine():
    assert (
        measured_segments(
            [dict(timestamp_seconds=0, source_frame_index=0, selected_f0_hz=70)], [], 70, 0.01
        )
        == []
    )
    assert all(
        not p["events"] and not p["paths"] for p in replay()["recordings"][2]["policies"].values()
    )


def test_group_stays_one_span_and_extreme_tail_is_explicit():
    r = replay()["recordings"][0]
    assert len(r["units"]) == 6
    assert {k: v for k, v in r["units"][-1].items() if k != "display_position_per_second"} == dict(
        key="5", label="雨伞", start_seconds=3.56, end_seconds=4.87, grouped=True
    )
    tail = r["segments"][-1]
    a, b = next((a, b) for a, b in pairwise(tail) if a["timestamp_seconds"] == 4.7047)
    assert b["normalized_semitones"] - a["normalized_semitones"] == pytest.approx(
        -11.5547, abs=0.0001
    )
    crossing = r["policies"]["mad3"]["crossings"][-1]
    assert crossing["timestamp_seconds"] == pytest.approx(4.712857203704743)
    assert r["policies"]["mad3"]["events"][-1]["source_indices"] == [468, 469, 470, 471]


def test_target_reference_independence_and_exact_x():
    data = replay()
    assert all(r["x_preserved"] for r in data["recordings"])
    r = data["recordings"][0]
    before = project_with_overflow(
        r["segments"], r["policies"]["mad3"]["domain"], r["units"], r["cadence"]
    )
    renamed = copy.deepcopy(r["units"])
    for u in renamed:
        u.update(label="别", target="target", pinyin="other", reference_tone=4)
    assert before == project_with_overflow(
        r["segments"], derive_mine_display_domain(r["segments"], "mad3"), renamed, r["cadence"]
    )


def test_clean_controls_zero_overflow_for_mad3():
    for r in replay()["recordings"][3:5]:
        assert not r["policies"]["mad3"]["events"]


def test_high_branch_duration_survives_but_whole_unit_shape_is_outside():
    p = replay()["recordings"][1]["policies"]["mad3"]
    high = p["units"][-1]
    assert high["overflow_points"] == 24 and high["inside_points"] == 0
    assert [e["duration_seconds"] for e in high["events"]] == pytest.approx([0.03, 0.21])
    assert high["overflow_support_fraction"] == pytest.approx(1)


def test_a5_excursions_are_two_explicit_runs():
    p = replay()["recordings"][5]["policies"]["mad3"]
    assert len(p["events"]) == 2 and p["overflow_points"] == 5
    assert [e["duration_seconds"] for e in p["events"]] == pytest.approx([0.03, 0.02])


def test_all_protected_low_points_still_present_even_if_outside():
    r = replay()
    assert r["protected_preserved"] == 617 and r["sub70_preserved"] == 11
    assert r["selected_control_preserved"] == 2827
    low = next(c for c in r["controls"] if c["id"] == "7787300e")
    explicit = next(p for s in low["segments"] for p in s if p["timestamp_seconds"] == 2.5124)
    assert explicit["selected_f0_hz"] == 54.61
    for policy in POLICIES:
        assert (
            low["policies"][policy]["inside_points"] + low["policies"][policy]["overflow_points"]
            == low["selected_count"]
        )


def test_coherent_large_sweep_and_continuous_jump_preserve_true_amplitude():
    r = replay()
    sweep = r["synthetic"][2]
    assert len(sweep["segments"]) == 1 and sweep["selected_count"] == 61
    p = sweep["segments"][0]
    assert p[-1]["normalized_semitones"] - p[0]["normalized_semitones"] == pytest.approx(24)
    assert sweep["policies"]["q90"]["overflow_points"] > 0
    assert len(sweep["policies"]["q90"]["events"]) == 2
    jump = r["synthetic"][1]["segments"]
    assert len(jump) == 1 and jump[0][2]["normalized_semitones"] - jump[0][1][
        "normalized_semitones"
    ] == pytest.approx(12)
    assert 12 * math.log2(
        jump[0][-1]["selected_f0_hz"] / jump[0][0]["selected_f0_hz"]
    ) == pytest.approx(13.650042, abs=0.000001)


def test_saved_more_detail_raw_and_all_original_evidence_are_unchanged():
    root = REPORT.parents[4]
    checked = 0
    for name, expected in replay()["input_sha256"].items():
        path = root / name
        if not path.exists():
            pytest.skip("private frozen snapshots unavailable")
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
        checked += 1
    assert checked == 30  # saved analyses, six tracks, 23 frozen controls


def test_boundary_sample_reentry_keeps_measured_vertex():
    p = project([6, 3, 0])
    assert p["paths"][0][0]["timestamp_seconds"] == 0.01
    assert p["paths"][0][0]["normalized_semitones"] == 3
    assert p["events"][0]["source_indices"] == [0]


def test_rejected_source_frame_and_missing_cadence_break_before_projection():
    frames = [
        dict(source_frame_index=i, timestamp_seconds=t, selected_f0_hz=hz)
        for i, t, hz in [(0, 0, 70), (1, 0.01, None), (2, 0.02, 70), (3, 0.05, 70)]
    ]
    segments = measured_segments(frames, UNITS, 70, 0.01)
    assert [[p["source_frame_index"] for p in s] for s in segments] == [[0], [2], [3]]

"""Fragment truth boundary, invariants, and frozen physical findings."""

from __future__ import annotations

import copy
import json
import math
from itertools import pairwise
from pathlib import Path

import pytest

from benchmark.pronunciation_v2.relative_pitch_fragments import (
    fragment_pairwise_error,
    relative_pitch_fragments,
)
from benchmark.pronunciation_v2.relative_pitch_gesture import Sample, Unit

REPORT = (
    Path(__file__).resolve().parents[2]
    / "docs/research/pronunciation-v2/2026-10-07-relative-pitch-gesture/fragment-replay.json"
)


def project(values, *, base=100, units=None):
    samples = [
        Sample(i, 0.01 * i, None if value is None else base * 2 ** (value / 12))
        for i, value in enumerate(values)
    ]
    return relative_pitch_fragments(
        samples, units or [Unit("group", 0, len(values) * 0.01, "fixture")], cadence_seconds=0.01
    )


def values(result):
    return [p["normalized_semitones"] for seg in result["segments"] for p in seg]


def indices(result):
    return [[p["source_frame_index"] for p in seg] for seg in result["segments"]]


def test_single_missing_frame_splits_and_never_connects():
    p = project([0, 1, None, 13, 14])
    assert indices(p) == [[0, 1], [3, 4]]
    assert values(p) == pytest.approx([-0.5, 0.5, -0.5, 0.5])
    f = p["units"][0]["fragments"][0]
    assert f["following_gap"]["intervening_source_frames"] == 1
    assert f["following_gap"]["elapsed_between_selected_seconds"] == pytest.approx(0.02)
    assert f["following_gap"]["missing_support_seconds"] == pytest.approx(0.01)


def test_continuous_giant_jump_must_remain_one_fragment():
    p = relative_pitch_fragments(
        [Sample(i, 0.01 * i, hz) for i, hz in enumerate([100, 105, 210, 220])],
        [Unit("one", 0, 0.04, "fixture")],
        cadence_seconds=0.01,
    )
    assert indices(p) == [[0, 1, 2, 3]]
    assert values(p)[2] - values(p)[1] == pytest.approx(12)
    assert p["units"][0]["fragments"][0]["excursion_semitones"] == pytest.approx(
        12 * math.log2(2.2)
    )


@pytest.mark.parametrize(
    "heights", [[0, 1, 2, 4], [4, 2, 1, 0], [3, 1, -2, 0, 4], [0, 1, 13, 14], [0, None, 3, 1, 2]]
)
def test_exact_pairs_extrema_curvature_amplitude_and_order(heights):
    p = project(heights)
    assert fragment_pairwise_error(p) < 1e-12
    for seg in p["segments"]:
        a = [q["absolute_semitones"] for q in seg]
        b = [q["normalized_semitones"] for q in seg]
        assert max(a) - min(a) == pytest.approx(max(b) - min(b))
        assert a.index(min(a)) == b.index(min(b)) and a.index(max(a)) == b.index(max(b))
        for i in range(1, len(a) - 1):
            assert b[i + 1] - 2 * b[i] + b[i - 1] == pytest.approx(
                a[i + 1] - 2 * a[i] + a[i - 1], abs=1e-12
            )
        assert [y > x for x, y in pairwise(a)] == [y > x for x, y in pairwise(b)]


@pytest.mark.parametrize("base", [54.61, 55, 60, 70, 350, 380, 440])
def test_same_shape_low_and_high_register(base):
    a = project([3, 1, 0, 2, None, 15, 13, 14], base=base)
    b = project([3, 1, 0, 2, None, 15, 13, 14])
    assert values(a) == pytest.approx(values(b), abs=1e-12)
    assert indices(a) == indices(b)


@pytest.mark.parametrize("shift", [-12, 12])
def test_octave_copy_equivalent_shared_domain_geometry(shift):
    contour = [3, 1, 0, 2, None, 15, 13, 14]
    a = project(contour)
    b = project([v + shift if v is not None else None for v in contour])

    def y(p):
        lo, hi = p["minimum_semitones"], p["maximum_semitones"]
        return [(v - lo) / (hi - lo) * 128 for v in values(p)]

    assert y(a) == pytest.approx(y(b), abs=1e-10)


def test_boundaries_do_not_depend_on_any_pitch_magnitude():
    a = project([0, 0, None, 0, 0, 0, None, 0])
    b = project([40, -40, None, -20, 40, -40, None, 50])
    assert indices(a) == indices(b)


def test_source_index_gap_and_time_gap_are_both_honored():
    samples = [Sample(0, 0.01, 100), Sample(2, 0.03, 100), Sample(3, 0.06, 100)]
    p = relative_pitch_fragments(samples, [Unit("one", 0, 0.1, "fixture")], cadence_seconds=0.01)
    assert indices(p) == [[0], [2], [3]]


def test_cadence_quantization_preserves_contiguous_runs():
    # Physical timestamps include 9.9 and 10.1 ms steps, far below the existing
    # 15 ms guard. A two-slot time step cannot be treated as measured continuity.
    samples = [Sample(0, 0.9218, 100), Sample(1, 0.9317, 200), Sample(2, 0.9418, 100)]
    p = relative_pitch_fragments(samples, [Unit("one", 0.9, 1, "fixture")], cadence_seconds=0.01)
    assert indices(p) == [[0, 1, 2]]
    samples.append(Sample(3, 0.9618, 100))
    p = relative_pitch_fragments(samples, [Unit("one", 0.9, 1, "fixture")], cadence_seconds=0.01)
    assert indices(p) == [[0, 1, 2], [3]]


def test_group_identity_one_span_with_multiple_fragments():
    p = project([0, 2, None, 12, 14])
    assert len(p["units"]) == 1 and p["units"][0]["key"] == "group"
    assert p["units"][0]["fragment_count"] == 2
    assert p["units"][0]["start_seconds"] == 0 and p["units"][0]["end_seconds"] == 0.05
    assert all(q["unit_key"] == "group" for seg in p["segments"] for q in seg)


def test_character_and_group_use_same_acoustic_logic():
    a = project([0, 2, None, 12, 14], units=[Unit("one", 0, 0.05, "word")])
    b = project([0, 2, None, 12, 14], units=[Unit("one", 0, 0.05, "character")])
    assert a["segments"] == b["segments"]


def test_no_timing_no_pitch_and_no_empty_fragment_invention():
    p = relative_pitch_fragments([Sample(0, 0.01, 100)], [], cadence_seconds=0.01)
    assert p["segments"] == [] and p["units"] == []
    p = project([None, None])
    assert p["segments"] == [] and p["units"][0]["fragment_count"] == 0


def test_shared_domain_does_not_equalize_amplitudes():
    p = project([0, 2, None, 10, 18])
    a, b = p["segments"]
    assert (a[-1]["normalized_semitones"] - a[0]["normalized_semitones"]) / (
        b[-1]["normalized_semitones"] - b[0]["normalized_semitones"]
    ) == pytest.approx(0.25)


def test_input_is_not_mutated_and_original_indices_times_survive():
    s = [Sample(i, 0.01 * i, hz) for i, hz in enumerate([100, None, 110, 220])]
    u = [Unit("one", 0, 0.04, "fixture")]
    before = copy.deepcopy((s, u))
    p = relative_pitch_fragments(s, u, cadence_seconds=0.01)
    assert (s, u) == before
    assert [
        (x["source_frame_index"], x["timestamp_seconds"]) for seg in p["segments"] for x in seg
    ] == [(0, 0), (2, 0.02), (3, 0.03)]


def replay():
    return json.loads(REPORT.read_text())


def test_primary_group_three_real_fragments_and_continuous_tail_exposed():
    r = replay()["recordings"][0]
    u = r["projection"]["units"][-1]
    assert u["label"] == "雨伞" and u["grouped"]
    assert (u["start_seconds"], u["end_seconds"]) == (3.56, 4.87)
    assert [f["selected_count"] for f in u["fragments"]] == [54, 4, 21]
    assert [f["following_gap"]["intervening_source_frames"] for f in u["fragments"][:-1]] == [
        18,
        22,
    ]
    tail = u["fragments"][-1]
    assert tail["excursion_semitones"] == pytest.approx(11.7237, abs=0.0001)
    assert tail["maximum_adjacent_step_st"] == pytest.approx(11.5547, abs=0.0001)
    assert tail["source_indices"] == list(
        range(tail["source_indices"][0], tail["source_indices"][-1] + 1)
    )


def test_high_branch_split_only_at_already_rejected_frame():
    u = replay()["recordings"][1]["projection"]["units"][-1]
    assert u["label"] == "果"
    assert [f["selected_count"] for f in u["fragments"]] == [3, 21]
    assert u["fragments"][0]["end_seconds"] == 4.1202
    assert u["fragments"][1]["start_seconds"] == 4.1402
    assert u["fragments"][0]["following_gap"]["intervening_source_frames"] == 1
    assert sum(f["selected_count"] for f in u["fragments"]) == 24


def test_a5_high_excursions_are_disconnected_and_not_split_on_frequency():
    r = replay()["recordings"][5]
    units = r["projection"]["units"]
    assert [f["selected_count"] for f in units[1]["fragments"]] == [29, 3]
    assert [f["selected_count"] for f in units[3]["fragments"]] == [14, 2]
    assert units[1]["fragments"][0]["following_gap"]["intervening_source_frames"] == 1
    assert units[3]["fragments"][0]["following_gap"]["intervening_source_frames"] == 3
    assert r["fragment_domain"] == pytest.approx([-6.33077, 5.59342], abs=0.00001)


def test_six_take_counts_x_mapping_metadata_and_preservation():
    r = replay()
    assert [x["fragment_count"] for x in r["recordings"]] == [12, 13, 0, 6, 6, 8]
    assert [x["projected_count"] for x in r["recordings"]] == [252, 188, 0, 224, 161, 136]
    assert all(
        x["target_independence"] and x["input_unchanged"] and x["horizontal_positions_unchanged"]
        for x in r["recordings"]
    )
    assert not r["production_integration"] and r["outcome"] == "B"
    assert r["controls"]["protected_preserved"] == 617
    assert r["controls"]["sub70_preserved"] == 11
    assert r["controls"]["selected_preserved"] == 2827

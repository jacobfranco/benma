"""Focused research invariants and frozen physical acceptance findings."""

from __future__ import annotations

import copy
import json
import math
from itertools import pairwise
from pathlib import Path

import pytest

from benchmark.pronunciation_v2.relative_pitch_gesture import (
    Sample,
    Unit,
    pairwise_error,
    project_relative,
)

REPORT = (
    Path(__file__).resolve().parents[2]
    / "docs/research/pronunciation-v2/2026-10-07-relative-pitch-gesture/replay.json"
)


def samples(heights, base=100):
    return [
        Sample(i, i * 0.01, None if v is None else base * 2 ** (v / 12))
        for i, v in enumerate(heights)
    ]


def projection(heights, base=100):
    return project_relative(
        samples(heights, base), [Unit("one", 0, len(heights) * 0.01, "fixture")]
    )


def heights(result):
    return [p["normalized_semitones"] for s in result["segments"] for p in s]


def geometry(result):
    lo, hi = result["minimum_semitones"], result["maximum_semitones"]
    return [
        (p["timestamp_seconds"], (p["normalized_semitones"] - lo) / (hi - lo))
        for s in result["segments"]
        for p in s
    ]


@pytest.mark.parametrize("shift", [-12, 12])
def test_octave_equivalent_geometry(shift):
    contour = [0, 1, 4, None, 2, -1, 3]
    a = projection(contour)
    b = projection([None if p is None else p + shift for p in contour])
    for x, y in zip(geometry(a), geometry(b), strict=True):
        assert x == pytest.approx(y, abs=1e-12)
    assert [len(s) for s in a["segments"]] == [len(s) for s in b["segments"]]


@pytest.mark.parametrize(
    "contour", [[0, 1, 2, 4], [4, 2, 1, 0], [4, 1, -2, 0, 3], [0, 1, 13, 14], [0, None, 4, -2, 0]]
)
def test_every_pair_order_extrema_curvature_amplitude(contour):
    result = projection(contour)
    source = [p for p in contour if p is not None]
    relative = heights(result)
    assert pairwise_error(result) < 1e-12
    for i, a in enumerate(source):
        for j, b in enumerate(source):
            assert relative[j] - relative[i] == pytest.approx(b - a, abs=1e-12)
    assert max(relative) - min(relative) == pytest.approx(max(source) - min(source))
    assert [b - a > 0 for a, b in pairwise(relative)] == [b - a > 0 for a, b in pairwise(source)]
    assert relative.index(min(relative)) == source.index(min(source))
    for i in range(1, len(relative) - 1):
        assert relative[i + 1] - 2 * relative[i] + relative[i - 1] == pytest.approx(
            source[i + 1] - 2 * source[i] + source[i - 1], abs=1e-12
        )


@pytest.mark.parametrize("hz", [54.61, 55, 60, 70, 350, 380, 440])
def test_register_independent_shape(hz):
    assert heights(projection([1, -1, 0, 3], hz)) == pytest.approx(
        heights(projection([1, -1, 0, 3])), abs=1e-12
    )


def test_gaps_indices_times_and_input_immutability():
    source = [
        Sample(5, 0.1, 100),
        Sample(6, 0.11, 105),
        Sample(7, 0.12, None),
        Sample(8, 0.13, 110),
        Sample(10, 0.15, 115),
        Sample(11, 0.3, 120),
    ]
    before = copy.deepcopy(source)
    r = project_relative(source, [Unit("one", 0, 1, "fixture")])
    assert [[p["source_frame_index"] for p in s] for s in r["segments"]] == [
        [5, 6],
        [8],
        [10],
        [11],
    ]
    assert [p["timestamp_seconds"] for s in r["segments"] for p in s] == [
        0.1,
        0.11,
        0.13,
        0.15,
        0.3,
    ]
    assert source == before


def test_group_one_center_and_no_cross_unit_connector():
    source = samples([0, 2, 12, 14, 20, 22])
    r = project_relative(
        source, [Unit("group", 0, 0.04, "word"), Unit("next", 0.04, 0.06, "character")]
    )
    assert len(r["units"]) == 2
    assert heights(r)[:4] == pytest.approx([-7, -5, 5, 7])
    assert [len(s) for s in r["segments"]] == [4, 2]
    assert all(len({p["unit_key"] for p in s}) == 1 for s in r["segments"])
    assert r["units"][0]["relative_range"] == pytest.approx([-7, 7])


def test_shared_domain_preserves_relative_amplitudes():
    r = project_relative(
        samples([0, 2, 20, 28]),
        [Unit("small", 0, 0.02, "fixture"), Unit("large", 0.02, 0.04, "fixture")],
    )
    y = [p[1] for p in geometry(r)]
    assert (y[1] - y[0]) / (y[3] - y[2]) == pytest.approx(2 / 8)


def test_no_timing_and_empty_unit_never_create_pitch():
    r = project_relative(samples([0, 1, 2]), [])
    assert r["segments"] == [] and r["units"] == []
    r = project_relative(samples([None, None]), [Unit("empty", 0, 0.1, "fixture")])
    assert r["segments"] == [] and r["units"][0]["center_hz"] is None


@pytest.mark.parametrize("source", ["synthetic", "equal_split", "synthetic_replay", ""])
def test_synthetic_timing_rejected(source):
    with pytest.raises(ValueError, match="untrusted"):
        project_relative(samples([0]), [Unit("bad", 0, 1, source)])


def test_half_open_boundary_and_overlap_owner():
    r = project_relative(
        [Sample(0, 0.1, 100), Sample(1, 0.2, 110), Sample(2, 0.3, 120)],
        [Unit("a", 0, 0.2005, "fixture"), Unit("b", 0.2, 0.3, "fixture")],
    )
    assert [[p["source_frame_index"] for s in u["segments"] for p in s] for u in r["units"]] == [
        [0],
        [1],
    ]


def test_mid_unit_octave_switch_is_not_fixed_or_hidden():
    r = project_relative(
        [Sample(i, i * 0.01, hz) for i, hz in enumerate([100, 105, 210, 220])],
        [Unit("one", 0, 0.04, "fixture")],
    )
    assert heights(r)[2] - heights(r)[1] == pytest.approx(12)
    assert r["maximum_semitones"] - r["minimum_semitones"] > 15


def replay():
    return json.loads(REPORT.read_text())


def test_six_take_truth_boundaries_and_rejected_acceptance():
    r = replay()
    assert not r["production_integration"] and r["outcome"] == "B"
    assert [x["timing_units"] for x in r["recordings"]] == [6, 6, 0, 6, 6, 6]
    assert [x["projected_count"] for x in r["recordings"]] == [252, 188, 0, 224, 161, 136]
    for row in r["recordings"]:
        assert row["pairwise_error"] < 1e-12
    no_timing = r["recordings"][2]
    assert no_timing["selected_count"] == 214 and no_timing["relative"]["segments"] == []
    umbrella = r["recordings"][0]["relative"]["units"][-1]
    assert umbrella["label"] == "雨伞" and umbrella["grouped"]
    assert umbrella["selected_count"] == 79
    assert r["recordings"][0]["domain_span_ratio"] > 0.96
    assert r["recordings"][5]["domain_span_ratio"] > 1.12


def test_high_branch_full_unit_survives_without_setting_extrema():
    row = replay()["recordings"][1]
    unit = row["relative"]["units"][-1]
    assert unit["label"] == "果" and unit["selected_count"] == 24
    assert unit["hz_range"] == pytest.approx([353.148, 433.949], abs=0.01)
    assert unit["relative_range"] == pytest.approx([-0.759, 2.813], abs=0.01)
    pts = [p for s in unit["segments"] for p in s]
    assert pts[0]["timestamp_seconds"] == 4.1002 and pts[-1]["timestamp_seconds"] == 4.3402
    assert len(unit["segments"]) == 2
    assert not unit["large_selected_steps"]
    assert row["relative_domain"][0] < -10 and row["relative_domain"][1] > 17


def test_protected_low_replay_and_known_failures_are_explicit():
    r = replay()
    assert r["controls"]["protected_preserved"] == 617
    assert r["controls"]["under70_preserved"] == 11
    assert any(p["raw_f0_hz"] == 54.61 for p in r["controls"]["under70"])
    # Six units with large steps; 要 remains a genuine-low-dip alternative,
    # not an asserted tracker error. Five other units retain reviewed artifacts.
    assert (
        sum(
            bool(u["large_selected_steps"])
            for row in r["recordings"]
            for u in row["relative"]["units"]
        )
        == 6
    )


def test_synthetic_high_movement_retained():
    r = project_relative(
        [Sample(i, 0.01 * i, hz) for i, hz in enumerate([350, 380, 410, 440])],
        [Unit("falsetto_control", 0, 0.04, "fixture")],
    )
    assert heights(r)[-1] - heights(r)[0] == pytest.approx(12 * math.log2(440 / 350))
    assert len(heights(r)) == 4


def test_real_mobile_geometry_reference_independence_and_input_preservation():
    for row in replay()["recordings"]:
        assert row["target_independence"] and row["input_unchanged"]


def test_presentation_cannot_change_existing_eligibility_or_observation():
    from benma_api.pronunciation.contours import classify_contour
    from benma_api.pronunciation.pitch_evidence import interpretation_eligibility
    from benma_api.pronunciation.pitch_types import PitchRegionProjection, UtterancePitchTrack
    from benma_api.schemas import DisplayContour

    from benchmark.pronunciation_v2.relative_pitch_report import LOCAL, ROOT, accepted_units

    capture = LOCAL / "saved-analyses.json"
    if not capture.exists():
        pytest.skip("private six-take snapshots unavailable")
    count = 0
    for saved in json.loads(capture.read_text()):
        data = saved["analyses"][-1]["result"]
        frozen = json.loads(
            (
                ROOT / "services/api/var/octave-ambiguity/before" / (saved["id"] + ".json")
            ).read_text()
        )
        track = UtterancePitchTrack.model_validate(frozen["track"])
        raw = frozen["result"]["f0"]
        display = DisplayContour.model_validate(data["display_contour"])
        snapshot = track.model_dump_json()
        for u, _, _, original in accepted_units(data):
            region = PitchRegionProjection.model_validate(original["pitch_projection"])
            before = interpretation_eligibility(track, region)
            observed = classify_contour(display, u.start, u.end, raw=raw, pitch_track=track)
            altered = display.model_copy(update={"segments": []})
            assert classify_contour(altered, u.start, u.end, raw=raw, pitch_track=track) == observed
            assert interpretation_eligibility(track, region) == before
            count += 1
        assert track.model_dump_json() == snapshot
    assert count == 30

"""Composition invariants and frozen acceptance counterexamples; no acoustics."""

import copy
import hashlib
import math
import statistics
from functools import lru_cache
from itertools import pairwise

import pytest

from benchmark.pronunciation_v2.composed_relative_overflow import (
    POLICIES,
    center_timing_units,
    compose,
    relative_domain,
)
from benchmark.pronunciation_v2.relative_pitch_report import LOCAL, REPORT, ROOT, SAVED, read
from benchmark.pronunciation_v2.robust_domain_overflow import (
    derive_mine_display_domain,
    project_with_overflow,
)


@lru_cache
def replay():
    return read(REPORT / "composed-replay.json")


def fixture(values, key="0", start=0):
    unit = dict(key=key, label=key, start_seconds=start, end_seconds=start + len(values) * 0.01)
    points = [
        dict(
            source_frame_index=i,
            timestamp_seconds=start + i * 0.01,
            position=i / len(values),
            unit_key=key,
            selected_f0_hz=70 * 2 ** (v / 12),
            normalized_semitones=v,
        )
        for i, v in enumerate(values)
    ]
    return [points], [unit]


@pytest.mark.parametrize(
    "values", [[0, 1, 2, 3], [3, 2, 1, 0], [3, 1, 0, 1, 3], [0, 3, 1, 4, -12, 0]]
)
def test_constant_translation_keeps_pairs_slopes_extrema_curvature_and_amplitude(values):
    source, units = fixture(values)
    result, _ = center_timing_units(source, units)
    relative = [p["normalized_semitones"] for p in result[0]]
    for i, a in enumerate(values):
        for j, b in enumerate(values):
            assert relative[j] - relative[i] == pytest.approx(b - a, abs=1e-12)
    assert max(relative) - min(relative) == pytest.approx(max(values) - min(values))
    for i in range(1, len(values) - 1):
        assert relative[i - 1] - 2 * relative[i] + relative[i + 1] == pytest.approx(
            values[i - 1] - 2 * values[i] + values[i + 1], abs=1e-12
        )
        assert (relative[i] > relative[i - 1] and relative[i] > relative[i + 1]) == (
            values[i] > values[i - 1] and values[i] > values[i + 1]
        )
        assert (relative[i] < relative[i - 1] and relative[i] < relative[i + 1]) == (
            values[i] < values[i - 1] and values[i] < values[i + 1]
        )


def test_all_physical_points_gaps_x_timestamps_hz_and_input_unchanged():
    previous = read(LOCAL / "overflow/viewer-data.json")
    total = 0
    for old, row in zip(previous["recordings"], replay()["recordings"], strict=True):
        source = copy.deepcopy(old["segments"])
        result = compose(source, old["units"], old["cadence"])
        assert source == old["segments"]
        assert result["segments"] == row["segments"]
        for a, b in zip(source, result["segments"], strict=True):
            assert len(a) == len(b)
            for p, q in zip(a, b, strict=True):
                assert {k: v for k, v in p.items() if k != "normalized_semitones"} == {
                    k: v
                    for k, v in q.items()
                    if k not in {"normalized_semitones", "absolute_semitones"}
                }
                total += 1
        for unit in row["units"]:
            points = [p for s in row["segments"] for p in s if p["unit_key"] == unit["key"]]
            for a in points:
                for b in points:
                    assert b["normalized_semitones"] - a["normalized_semitones"] == pytest.approx(
                        12 * math.log2(b["selected_f0_hz"] / a["selected_f0_hz"]), abs=1e-12
                    )
    assert total == 961


@pytest.mark.parametrize("factor", [0.5, 2])
def test_independent_unit_register_shifts_leave_all_mine_geometry_identical(factor):
    for row in replay()["recordings"]:
        shifted = copy.deepcopy(row["segments"])
        for s in shifted:
            for p in s:
                # Alternate units only: cross-unit register changes are real.
                if int(p["unit_key"]) % 2:
                    p["selected_f0_hz"] *= factor
        result = compose(shifted, row["units"], 0.01)
        for a, b in zip(row["segments"], result["segments"], strict=True):
            assert [p["normalized_semitones"] for p in a] == pytest.approx(
                [p["normalized_semitones"] for p in b], abs=1e-11
            )
        for policy in POLICIES:
            a, b = row["policies"][policy], result["policies"][policy]
            assert a["domain"] == pytest.approx(b["domain"], abs=1e-11)
            assert a["overflow_points"] == b["overflow_points"]
            for pa, pb in zip(a["paths"], b["paths"], strict=True):
                for qa, qb in zip(pa, pb, strict=True):
                    assert qa == pytest.approx(qb, abs=1e-11)
            for ea, eb in zip(a["events"], b["events"], strict=True):
                assert ea == pytest.approx(eb, abs=1e-11)


def test_group_centered_once_across_all_real_gaps_and_no_cross_unit_connector():
    row = replay()["recordings"][0]
    group = row["units"][-1]
    assert (group["label"], group["start_seconds"], group["end_seconds"]) == ("雨伞", 3.56, 4.87)
    segments = [s for s in row["segments"] if s[0]["unit_key"] == group["key"]]
    assert [len(s) for s in segments] == [54, 4, 21]
    assert group["center_semitones_re_1hz"] == statistics.median(
        p["absolute_semitones"] for s in segments for p in s
    )
    for s in segments:
        for p in s:
            assert p["absolute_semitones"] - p["normalized_semitones"] == pytest.approx(
                group["center_semitones_re_1hz"]
            )
    for r in replay()["recordings"]:
        for path in r["policies"]["mad3.5"]["paths"]:
            owners = [
                u
                for u in r["units"]
                if all(
                    u["start_seconds"] <= p["timestamp_seconds"] < u["end_seconds"] for p in path
                )
            ]
            assert len(owners) == 1


def test_terminal_continuous_drop_intersection_and_duration_are_analytical():
    row = replay()["recordings"][0]
    a, b = next(
        (a, b) for s in row["segments"] for a, b in pairwise(s) if a["timestamp_seconds"] == 4.7047
    )
    delta = b["normalized_semitones"] - a["normalized_semitones"]
    assert delta == pytest.approx(-11.5547, abs=0.0001)
    for p in row["policies"].values():
        f = (p["domain"][0] - a["normalized_semitones"]) / delta
        crossing = p["crossings"][-1]
        assert crossing["timestamp_seconds"] == pytest.approx(4.7047 + f * 0.01)
        assert crossing["position"] == pytest.approx(
            a["position"] + f * (b["position"] - a["position"])
        )
        event = p["events"][-1]
        assert event["source_indices"] == [468, 469, 470, 471]
        assert event["duration_seconds"] == pytest.approx(4.7497 - crossing["timestamp_seconds"])


def test_composed_sustained_run_reentry_and_gap_remain_explicit():
    segments, units = fixture([0] * 15 + [12] * 24 + [0] * 15)
    result = compose(segments, units, 0.01)["policies"]["mad3"]
    assert len(result["events"]) == 1
    assert result["events"][0]["duration_seconds"] == pytest.approx(0.245)
    assert result["crossings"][0]["timestamp_seconds"] == pytest.approx(0.1425)
    assert result["crossings"][1]["timestamp_seconds"] == pytest.approx(0.3875)
    assert len(result["paths"]) == 2
    split = [segments[0][:25], segments[0][26:]]
    projected = compose(split, units, 0.01)["policies"]["mad3"]
    assert len(projected["events"]) == 2
    assert (
        projected["events"][0]["support_end_seconds"]
        < projected["events"][1]["support_start_seconds"]
    )


def test_high_unit_now_visible_and_no_physical_unit_entirely_outside():
    high = replay()["recordings"][1]
    for policy in POLICIES:
        unit = high["policies"][policy]["units"][-1]
        assert unit["label"] == "果" and unit["inside_points"] == 24
        assert not unit["events"]
        assert unit["relative_range"] == pytest.approx([-0.755370783974, 2.811589434509])
        for r in replay()["recordings"]:
            assert not r["policies"][policy]["entirely_outside_units"]


def test_clean_controls_require_nearby_3_5_setting():
    a, b = replay()["recordings"][3:5]
    assert not a["policies"]["mad3.5"]["events"]
    assert not b["policies"]["mad3.5"]["events"]
    assert b["policies"]["mad3"]["overflow_points"] == 3
    assert b["policies"]["mad2.5"]["overflow_points"] == 5


def test_a5_ordinary_motion_overflow_remains_acceptance_counterexample():
    row = replay()["recordings"][5]
    p = row["policies"]["mad3.5"]
    assert p["overflow_points"] == 16 and len(p["events"]) == 5
    assert p["affected_units"] == ["有", "个", "苹", "果"]
    apple = p["units"][4]
    assert apple["overflow_support_fraction"] > 0.27
    assert apple["overflow_points"] == 7
    assert apple["excursion_semitones"] == pytest.approx(8.472342685835, abs=1e-10)
    assert row["absolute_robust_burden"]["overflow_points"] == 5


def test_no_timing_stays_empty_and_unowned_points_cannot_create_unit():
    row = replay()["recordings"][2]
    assert not row["units"] and not row["segments"]
    for p in row["policies"].values():
        assert not p["events"] and not p["paths"]
    segments, _ = fixture([0, 1])
    with pytest.raises(ValueError, match="accepted timing"):
        compose(segments, [], 0.01)
    assert compose([], [], 0.01)["centered_domain"] == [-3, 3]


def test_actual_protected_samples_and_all_sub70_entries_retained_exactly():
    protected = {r["recording"]: r["times"] for r in read(SAVED / "low-f0-proxy-samples.json")}
    sub70 = read(
        ROOT / "docs/research/pronunciation-v2/2026-10-05-utterance-evidence/low-f0-replay.json"
    )
    kept = count = 0
    for c in replay()["controls"]:
        saved = read(SAVED / "production" / (c["id"] + ".json"))
        source = {p["timestamp_seconds"]: p["f0_hz"] for p in saved["result"]["f0"]}
        points = {p["timestamp_seconds"]: p for s in c["segments"] for p in s}
        assert set(points) == set(saved["retained_times"])
        for t, p in points.items():
            assert p["selected_f0_hz"] == source[t]
        assert set(protected.get(c["id"], [])) <= points.keys()
        kept += len(protected.get(c["id"], []))
        count += len(points)
        for p in sub70:
            if p["recording"] == c["id"]:
                assert points[p["timestamp"]]["selected_f0_hz"] == source[p["timestamp"]]
        if c["id"] == "7787300e":
            assert points[2.5124]["selected_f0_hz"] == 54.61
    assert kept == 617 and count == 2827 and len(sub70) == 11


@pytest.mark.parametrize("hz", [54.61, 70, 350, 380, 440])
def test_coherent_absolute_register_is_only_constant_offset(hz):
    s, u = fixture([2, 1, 0, 1, 2])
    for p in s[0]:
        p["selected_f0_hz"] *= hz / 70
    p = compose(s, u, 0.01)
    assert [v["normalized_semitones"] for v in p["segments"][0]] == pytest.approx([1, 0, -1, 0, 1])
    assert all(not v["events"] for v in p["policies"].values())


def test_24st_sweep_alone_and_among_ordinary_units_keeps_full_movement():
    alone = replay()["synthetic"][2]
    mixed = replay()["mixed_sweep"]
    for row in [alone, mixed]:
        points = row["segments"][0]
        assert len(points) == 61
        assert points[-1]["normalized_semitones"] - points[0][
            "normalized_semitones"
        ] == pytest.approx(24)
    assert not alone["policies"]["mad3.5"]["events"]
    p = mixed["policies"]["mad3.5"]
    # Median zero and raw MAD one across this fixed control mixture.
    half_span = 1 + 3.5 * 1.4826
    assert p["domain"] == [-half_span, half_span]
    assert p["overflow_points"] == 30
    assert len(p["events"]) == 2
    assert [c["timestamp_seconds"] for c in p["crossings"]] == pytest.approx(
        [(12 - half_span) / 40, (12 + half_span) / 40]
    )


def test_reference_independence_and_shared_domain_match_prior_mad_family():
    for row in replay()["recordings"]:
        renamed = copy.deepcopy(row["units"])
        for u in renamed:
            u.update(
                label="别",
                target="x",
                perceived_character="字",
                pinyin="none",
                reference_tone=4,
                contextual_surface_tone=1,
            )
        projected = compose(row["segments"], renamed, 0.01)
        for policy in POLICIES:
            for key in ["domain", "paths", "crossings", "events"]:
                assert projected["policies"][policy][key] == row["policies"][policy][key]
        assert relative_domain(row["segments"], 3) == derive_mine_display_domain(
            row["segments"], "mad3"
        )
        for unit in row["policies"]["mad3.5"]["units"]:
            assert unit["domain"] == row["policies"]["mad3.5"]["domain"]


def test_sources_more_detail_raw_acoustic_metadata_and_production_unchanged():
    for name, expected in replay()["input_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
    for name, expected in read(LOCAL / "composed/production-before-sha256.json").items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected


def test_outside_evidence_accounted_for_by_visible_points_or_overflow_events():
    for row in [*replay()["recordings"], *replay()["controls"], replay()["mixed_sweep"]]:
        for p in row["policies"].values():
            low, high = p["domain"]
            outside = {
                v["source_frame_index"]
                for s in row["segments"]
                for v in s
                if not low <= v["normalized_semitones"] <= high
            }
            explicit = {i for e in p["events"] for i in e["source_indices"]}
            assert outside == explicit
            assert p["inside_points"] + p["overflow_points"] == sum(map(len, row["segments"]))


def test_invalid_mixed_unit_segment_and_nonfinite_selected_value_rejected_loudly():
    s, u = fixture([0, 1])
    s[0][1]["unit_key"] = "another"
    with pytest.raises(ValueError, match="separate segments"):
        center_timing_units(s, u)
    s[0][1]["unit_key"] = "0"
    s[0][1]["selected_f0_hz"] = float("nan")
    with pytest.raises(ValueError, match="cannot silently reject"):
        center_timing_units(s, u)


def test_overflow_is_geometry_only_and_minimum_span_is_not_exaggerated_zoom():
    s, u = fixture([0, 0.01, 0])
    result = compose(s, u, 0.01)
    assert all(p["domain"] == [-3, 3] for p in result["policies"].values())
    before = copy.deepcopy(result["segments"])
    project_with_overflow(result["segments"], [-0.001, 0.001], u, 0.01)
    assert result["segments"] == before

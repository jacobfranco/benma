"""Research contracts and falsification controls; not production acceptance."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from benma_api.pronunciation.contours import classify_contour
from benma_api.pronunciation.pitch_evidence import (
    display_from_track,
    gate_observation,
    interpretation_eligibility,
    project_pitch,
)

from benchmark.pronunciation_v2.octave_ambiguity import experiment, parameter_neighborhood
from benchmark.pronunciation_v2.octave_ambiguity_report import (
    check_preservation,
    make_track,
    masked_track,
)


def frames(hz: list[float | None]) -> list[dict]:
    return [
        dict(
            timestamp_seconds=round(i * 0.01, 4),
            raw_f0_hz=h,
            selected_f0_hz=h,
            periodicity=0.85,
            candidates=[dict(frequency_hz=h, strength=0.85)] if h else [],
        )
        for i, h in enumerate(hz)
    ]


@pytest.mark.parametrize("hz,alternate", [(55, 110), (220, 110), (440, 110)])
@pytest.mark.parametrize("gap", [False, True])
def test_candidate_supported_short_branch_across_gap(hz, alternate, gap):
    data = frames([110.0] * 20 + [hz] * 4 + [110.0] * 20)
    if gap:
        data[19] = frames([None])[0] | {"timestamp_seconds": 0.19}
    for f in data[20:24]:
        f["candidates"].append(dict(frequency_hz=alternate, strength=0.8))
    before = copy.deepcopy(data)
    for params in parameter_neighborhood().values():
        for consensus in (False, True):
            assert experiment(data, params, require_complete_run=consensus)[
                "rejected_indices"
            ] == list(range(20, 24))
    assert data == before


@pytest.mark.parametrize("hz", [55, 60, 70])
def test_coherent_low_f0_with_octave_candidates_survives(hz):
    data = frames([hz * 2 ** (-i / 200) for i in range(60)])
    for f in data:
        f["candidates"].append(dict(frequency_hz=2 * f["selected_f0_hz"], strength=0.8))
    assert not experiment(data)["rejected_indices"]


@pytest.mark.parametrize("direction", [-1, 1])
def test_smooth_two_octave_sweep_with_close_candidates_survives(direction):
    sweep = [55 * 2 ** (i / 30) for i in range(61)]
    data = frames(sweep if direction > 0 else list(reversed(sweep)))
    for f in data:
        f["candidates"].append(dict(frequency_hz=f["selected_f0_hz"] * 2**-direction, strength=0.8))
    for params in parameter_neighborhood().values():
        assert not experiment(data, params)["rejected_indices"]


def test_large_transition_without_candidate_or_with_weak_alternative_is_not_rejected():
    data = frames([110.0] * 20 + [220.0] * 4 + [110.0] * 20)
    assert not experiment(data)["rejected_indices"]
    for f in data[20:24]:
        f["candidates"].append(dict(frequency_hz=110, strength=0.4))
    assert not experiment(data)["rejected_indices"]


def test_bounded_one_sided_context_and_true_boundary_without_context():
    data = frames([110.0] * 20 + [55.0] * 4)
    for f in data[20:]:
        f["candidates"].append(dict(frequency_hz=110, strength=0.8))
    assert experiment(data)["rejected_indices"] == [20, 21, 22, 23]
    assert not experiment(data[20:])["rejected_indices"]
    data = frames([110.0] * 20 + [None] * 20 + [55.0] * 4)
    for f in data[40:]:
        f["candidates"].append(dict(frequency_hz=110, strength=0.8))
    assert not experiment(data)["rejected_indices"]


def test_long_branch_is_not_split_to_evade_run_duration():
    data = frames([110.0] * 20 + [55.0] * 30 + [110.0] * 20)
    for f in data[20:50]:
        f["candidates"].append(dict(frequency_hz=110, strength=0.8))
    assert not experiment(data)["rejected_indices"]


def test_counterfactual_keeps_raw_and_group_projection_and_incomplete_eligibility():
    raw = [
        dict(
            timestamp_seconds=i / 100,
            tracker_f0_hz=110.0,
            f0_hz=110.0,
            voicing_probability=0.9,
            pitch_candidates=[dict(frequency_hz=110.0, strength=0.9)],
        )
        for i in range(50)
    ]
    result = dict(f0=raw, duration_seconds=0.5)
    before = copy.deepcopy(result)
    track = make_track(result)
    after = masked_track(track, list(range(30, 50)))
    check_preservation(track, after)
    assert result == before
    projected = project_pitch(after, 0, 0.5, timing_source="azure_word")
    assert projected.frame_indices == tuple(range(50))
    eligible = interpretation_eligibility(after, projected)
    assert eligible.state == "incomplete"
    observed = classify_contour(display_from_track(after), 0, 0.5, raw=raw, pitch_track=after)
    assert gate_observation(observed, eligible).classification == "unclear"
    for text in ("", "arbitrary", "完全不同"):
        assert (
            make_track(result | dict(transcript=text, target=text, pinyin=text, expected_tone=4))
            == track
        )


def test_frozen_real_low_f0_counterexample_falsifies_frame_rule_in_all_nearby_settings():
    # Numeric acoustic evidence only; this test records a failure of the proposed
    # rule. It must not be counted as passing the product's low-F0 acceptance gate.
    # Exact acoustic excerpt at 2.4824--2.5624 s; the preceding selected branch is
    # outside the bounded context. No identity or reference label enters replay.
    data = frames([55.853, 55.288, 54.773, 54.61, 107.282, 105.687, 103.845, 101.83, 99.965])
    for f, strength, candidate, alternative_strength in zip(
        data[:4],
        [0.7467, 0.8239, 0.8815, 0.8415],
        [103.586, 102.477, 109.068, 108.62],
        [0.5588, 0.4597, 0.5466, 0.7776],
        strict=True,
    ):
        f["periodicity"] = strength
        f["candidates"] = [
            dict(frequency_hz=f["selected_f0_hz"], strength=strength),
            dict(frequency_hz=candidate, strength=alternative_strength),
        ]
    for p in parameter_neighborhood().values():
        assert experiment(data, p)["rejected_indices"] == [3]
        assert not experiment(data, p, require_complete_run=True)["rejected_indices"]
    saved = (
        Path(__file__).resolve().parents[2]
        / "docs/research/pronunciation-v2/2026-10-07-octave-ambiguity/replay.json"
    )
    report = json.loads(saved.read_text())
    low = next(r for r in report["controls"] if r["id"] == "7787300e")
    assert low["under70_protected_lost"] == [2.5124]
    assert all(r["protected_lost"] == [2.5124] for r in low["neighborhood"].values())
    assert all(not r["consensus_protected_lost"] for r in low["neighborhood"].values())
    assert report["production_changed"] is False

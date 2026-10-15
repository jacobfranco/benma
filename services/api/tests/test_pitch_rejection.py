"""Rejection boundaries: synthetic audio and immutable physical tracker evidence."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pytest

from benma_api.pronunciation.pitch_evidence import (
    build_pitch_track,
    interpretation_eligibility,
    project_pitch,
)
from benma_api.pronunciation.pitch_rejection import (
    BACKGROUND_REASON,
    BRANCH_REASON,
    background_periodicity,
    reject_ambiguous_branches,
    reject_background_pitch,
)

SAVED = json.loads((Path(__file__).parent / "fixtures/pitch_robustness_physical.json").read_text())


def contour(primary=20, branch=3, alternate=True):
    def frame(t, hz, alt=None):
        return dict(
            timestamp_seconds=t,
            f0_hz=hz,
            tracker_f0_hz=hz,
            selected_f0_hz=hz,
            voicing_probability=0.9,
            quality_usable=True,
            comparison_f0_hz=hz,
            energy_rms=0.1,
            pitch_candidates=[dict(frequency_hz=hz, strength=0.9)]
            + ([dict(frequency_hz=alt, strength=0.8)] if alt else []),
        )

    first = [frame(i * 0.01, 140 - 25 * i / (primary - 1)) for i in range(primary)]
    last = [frame((primary + 2 + i) * 0.01, 65, 130 if alternate else None) for i in range(branch)]
    return first + last


def track(points):
    return build_pitch_track(
        dict(f0=points, duration_seconds=points[-1]["timestamp_seconds"] + 0.02),
        audio_sha256="synthetic",
        tracker_source="test",
        tracker_version="test",
        parameters={},
    )


def test_short_candidate_ambiguous_tail_is_exclusion_not_replacement():
    raw = contour()
    before = copy.deepcopy(raw)
    assert reject_ambiguous_branches(raw) == 3
    for a, b in zip(before, raw, strict=True):
        for key in ("tracker_f0_hz", "f0_hz", "pitch_candidates", "timestamp_seconds"):
            assert a[key] == b[key]
    selected = track(raw)
    assert all(f.selected_f0_hz == f.raw_f0_hz for f in selected.frames if f.selected_f0_hz)
    assert all(BRANCH_REASON in f.exclusion_reasons for f in selected.frames[-3:])
    region = project_pitch(selected, 0, selected.duration_seconds, timing_source="accepted")
    eligibility = interpretation_eligibility(selected, region)
    assert eligibility.state == "sufficient"
    assert eligibility.metrics.maximum_raw_jump_semitones > 6  # raw audit preserved
    assert eligibility.reasons == ("candidate_branch_excluded_primary_sufficient",)


@pytest.mark.parametrize(
    "kind", ["no_alternative", "comparable", "sustained", "chaos", "all_ambiguous", "weak_primary"]
)
def test_unsafe_paths_have_no_branch_certificate(kind):
    raw = contour(
        branch=20 if kind == "comparable" else 9 if kind == "sustained" else 3,
        alternate=kind != "no_alternative",
    )
    if kind == "chaos":
        extra = contour(primary=20, branch=3)
        for p in extra:
            p["timestamp_seconds"] += raw[-1]["timestamp_seconds"] + 0.02
        raw += extra
    if kind == "all_ambiguous":
        for p in raw[:20]:
            p["pitch_candidates"].append(dict(frequency_hz=p["tracker_f0_hz"] / 2, strength=0.9))
    if kind == "weak_primary":
        for p in raw[:20]:
            p["voicing_probability"] = 0.6
    assert reject_ambiguous_branches(raw) == 0
    selected = track(raw)
    eligibility = interpretation_eligibility(
        selected, project_pitch(selected, 0, selected.duration_seconds, timing_source="accepted")
    )
    assert eligibility.state != "sufficient"


def test_sustained_real_low_pitch_is_not_a_branch():
    raw = contour(primary=40, branch=0)
    for p in raw:
        hz = p["tracker_f0_hz"] / 2
        p.update(f0_hz=hz, tracker_f0_hz=hz, selected_f0_hz=hz, comparison_f0_hz=hz)
        p["pitch_candidates"] = [dict(frequency_hz=hz, strength=0.9)]
    assert reject_ambiguous_branches(raw) == 0
    assert all(f.selected_f0_hz for f in track(raw).frames)


def waveform(kind):
    rate = 16000
    t = np.arange(rate * 3) / rate
    envelope = ((t > 0.7) & (t < 2.1)).astype(float)
    # Harmonic low male control has speech-only F0 plus normal upper harmonics.
    f0 = 65 if kind == "low_voice" else 220
    voice = envelope * (
        0.15 * np.sin(2 * np.pi * f0 * t)
        + 0.2 * np.sin(2 * np.pi * 2 * f0 * t)
        + 0.12 * np.sin(2 * np.pi * 3 * f0 * t)
    )
    noise = 0.001 * np.random.default_rng(4).normal(size=t.size)
    hum = 0.15 * np.sin(2 * np.pi * 60 * t)
    if kind == "transient":
        hum *= (t > 0.1) & (t < 0.4)
    if kind in ("low_voice", "clean"):
        hum *= 0
    return voice + hum + noise, rate


@pytest.mark.parametrize(
    "kind,detected", [("hum", True), ("low_voice", False), ("clean", False), ("transient", False)]
)
def test_background_requires_persistent_non_speech_support(kind, detected):
    values, rate = waveform(kind)
    result = background_periodicity(values, rate)
    assert result["detected"] is detected
    points = [
        dict(
            tracker_f0_hz=60,
            selected_f0_hz=60,
            low_frequency_energy_fraction=0.66,
            quality_usable=True,
        ),
        dict(
            tracker_f0_hz=220,
            selected_f0_hz=220,
            low_frequency_energy_fraction=0.66,
            quality_usable=True,
        ),
        dict(
            tracker_f0_hz=60,
            selected_f0_hz=60,
            low_frequency_energy_fraction=0.1,
            quality_usable=True,
        ),
    ]
    assert reject_background_pitch(points, result) == (1 if detected else 0)
    assert points[1]["selected_f0_hz"] == 220
    assert points[2]["selected_f0_hz"] == 60
    assert points[0]["tracker_f0_hz"] == 60


def test_physical_branch_preserves_all_fourteen_primary_frames_and_raw_candidates():
    raw = copy.deepcopy(SAVED[1]["acoustic"]["result"]["f0"])
    original = copy.deepcopy(raw)
    assert reject_ambiguous_branches(raw) == 7  # whole island, crossing alignment ownership
    selected = track(raw)
    assert (
        sum(
            f.selected_f0_hz is not None
            for f in selected.frames
            if 1.5 <= f.timestamp_seconds <= 1.64
        )
        == 14
    )
    assert (
        next(p for p in raw if p.get("selection_reason") == BRANCH_REASON)["tracker_f0_hz"]
        == 58.433
    )
    assert [p["tracker_f0_hz"] for p in raw] == [p["tracker_f0_hz"] for p in original]
    assert [p["pitch_candidates"] for p in raw] == [p["pitch_candidates"] for p in original]
    assert all(
        f.selected_f0_hz is None for f in selected.frames if 1.67 <= f.timestamp_seconds <= 1.74
    )


def test_washer_is_noise_control_and_removes_previously_leaking_frames():
    saved = SAVED[0]
    background = saved["background_periodicity"]
    assert background["detected"] and background["dominated_quiet_windows"] == 27
    assert not SAVED[1]["background_periodicity"]["detected"]
    raw = copy.deepcopy(saved["acoustic"]["result"]["f0"])
    leaked = [
        p
        for p in raw
        if p["quality_usable"]
        and p["tracker_f0_hz"]
        and p["tracker_f0_hz"] < 80
        and 0.63 <= p["low_frequency_energy_fraction"] <= 0.69
    ]
    assert len(leaked) >= 10
    assert reject_background_pitch(raw, background) == 160
    assert all(
        p["selected_f0_hz"] is None and p["selection_reason"] == BACKGROUND_REASON for p in leaked
    )


def test_frozen_corrupted_mai_does_not_gain_a_branch_certificate():
    frozen = json.loads(
        (Path(__file__).parent / "fixtures/raw_tracker_mai_430fcc2e.json").read_text()
    )
    # Frozen raw fixture and complete earlier recordings are also replayed by the audit.
    frozen_raw = [copy.deepcopy(f["point"]) for f in frozen["frames"]]
    assert reject_ambiguous_branches(frozen_raw) == 0
    frozen_track = track(frozen_raw)
    assert (
        interpretation_eligibility(
            frozen_track, project_pitch(frozen_track, 1.2, 1.47, timing_source="accepted")
        ).state
        == "insufficient"
    )
    for saved in SAVED:
        raw = copy.deepcopy(saved["acoustic"]["result"]["f0"])
        reject_ambiguous_branches(raw)
        mai = saved["data"]["syllables"][2]
        assert not any(
            p.get("selection_reason") == BRANCH_REASON
            for p in raw
            if mai["start_seconds"] <= p["timestamp_seconds"] < mai["end_seconds"]
        )

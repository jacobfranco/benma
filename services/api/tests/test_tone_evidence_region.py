from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from test_readings_contours import raw_contour

from benma_api.pronunciation.contours import classify_contour, display_contour
from benma_api.pronunciation.evidence_region import select_tone_evidence


def supported(values):
    raw = raw_contour(values)
    for p in raw:
        p.update(
            energy_rms=0.1,
            comparison_f0_hz=p["f0_hz"],
            quality_usable=True,
            voicing_probability=0.95,
            filter_disagreement_st=0,
        )
    return raw


def weak_attack(values):
    raw = supported([-12, 5, 3, *values])
    for p in raw[:3]:
        p.update(energy_rms=0.02, voicing_probability=0.6)
    raw[0]["comparison_f0_hz"] = None
    return raw


@pytest.mark.parametrize(
    "values,label",
    [
        ([0] * 40, "1-like"),
        ([i / 6 for i in range(40)], "2-like"),
        ([abs(i - 20) / 4 for i in range(40)], "3-like"),
        ([-i / 6 for i in range(40)], "4-like"),
    ],
)
def test_supported_boundary_exclusion_does_not_choose_a_tone(values, label):
    raw = weak_attack(values)
    snapshot = copy.deepcopy(raw)
    region = select_tone_evidence(raw, 0, len(raw) * 0.01)
    assert region.selected and region.onset_frames == 3
    measured = classify_contour(display_contour(raw), 0, len(raw) * 0.01, raw=raw)
    assert measured.classification == label
    assert measured.confidence == "moderate"
    assert measured.features["tracker_instability_rejected"] == 0
    assert measured.features["whole_span_tracker_instability_rejected"] == 1
    assert (
        measured.features["full_span_coverage"]
        == measured.features["whole_span_full_span_coverage"]
    )
    assert measured.features["evidence_duration_seconds"] < measured.features["duration_seconds"]
    assert raw == snapshot


@pytest.mark.parametrize(
    "variant",
    [
        "continuous_initial",
        "zero_initial",
        "short_rhyme",
        "missing_support",
        "sustained_octave",
        "high_energy_attack",
    ],
)
def test_no_blanket_initial_removal(variant):
    raw = weak_attack([0] * 40)
    if variant == "continuous_initial":
        for p in raw:
            p["comparison_f0_hz"] = p["f0_hz"]
    elif variant == "zero_initial":
        raw = supported([0] * 40)
    elif variant == "short_rhyme":
        raw = weak_attack([0] * 9)
    elif variant == "missing_support":
        for p in raw:
            p.pop("energy_rms")
    elif variant == "sustained_octave":
        raw = supported([-12] * 15 + [0] * 30)
    elif variant == "high_energy_attack":
        for p in raw[:3]:
            p["energy_rms"] = 0.1
    assert not select_tone_evidence(raw, 0, len(raw) * 0.01).selected


def test_terminal_disagreement_is_excluded_only_when_fading():
    raw = supported([0] * 40 + [-12] * 5)
    for p in raw[-5:]:
        p.update(
            quality_usable=False, energy_rms=0.02, filter_disagreement_st=12, comparison_f0_hz=180
        )
    # Use the actual base frequency of the synthetic helper.
    for p in raw[-5:]:
        p["comparison_f0_hz"] = raw[0]["f0_hz"]
    region = select_tone_evidence(raw, 0, 0.45)
    assert region.selected and region.terminal_frames == 5
    measured = classify_contour(display_contour(raw), 0, 0.45, raw=raw)
    assert measured.classification == "1-like"
    raw.append({**raw[-1], "timestamp_seconds": 0.45, "f0_hz": None, "energy_rms": 0.1})
    assert not select_tone_evidence(raw, 0, 0.5).selected


@pytest.mark.parametrize("gap,length,expected", [(20, 2, "1-like"), (20, 12, "unclear")])
def test_interior_dropout_cannot_be_segmented_away(gap, length, expected):
    raw = weak_attack([0] * 50)
    for p in raw[gap : gap + length]:
        p["f0_hz"] = None
    region = select_tone_evidence(raw, 0, 0.53)
    assert region.start < raw[gap]["timestamp_seconds"] < region.end
    measured = classify_contour(display_contour(raw), 0, 0.53, raw=raw)
    assert measured.classification == expected


def test_bad_core_is_not_rescued_by_clean_boundaries():
    raw = weak_attack([0 if i % 4 else -12 for i in range(50)])
    result = classify_contour(display_contour(raw), 0, 0.53, raw=raw)
    assert result.classification == "unclear"
    assert result.features["tracker_instability_rejected"] == 1


@pytest.mark.parametrize("padding", [0.1, 0.4])
def test_unvoiced_initial_and_benign_padding_preserve_coherent_tone(padding):
    raw = supported([-i / 5 for i in range(18)])
    for p in raw:
        p["timestamp_seconds"] += padding
    # Provider-aligned syllable excludes arbitrary recording padding.
    measured = classify_contour(display_contour(raw), padding - 0.04, padding + 0.23, raw=raw)
    assert measured.classification == "4-like"


def test_high_energy_unvoiced_rhyme_is_not_declared_a_benign_offset():
    raw = supported([-i / 10 for i in range(14)])
    raw += [
        {
            **raw[-1],
            "timestamp_seconds": i * 0.01,
            "f0_hz": None,
            "voicing_probability": 0,
            "energy_rms": 0.2,
        }
        for i in range(14, 50)
    ]
    assert not select_tone_evidence(raw, 0, 0.5).selected
    assert classify_contour(display_contour(raw), 0, 0.5, raw=raw).classification == "unclear"


def test_new_phone_and_non_ma_persisted_evidence():
    rows = json.loads((Path(__file__).parent / "fixtures" / "architecture_pitch.json").read_text())
    for row in rows:
        raw = row["raw"]
        snapshot = copy.deepcopy(raw)
        for s in row["spans"]:
            actual = classify_contour(display_contour(raw), s["start"], s["end"], raw=raw)
            assert (actual.classification, actual.reason) == (s["classification"], s["reason"])
        assert raw == snapshot


def test_synthetic_timing_cannot_authorize_region_grading():
    raw = weak_attack([0] * 40)
    result = classify_contour(display_contour(raw), 0, 0.43, raw=raw, timing_reliable=False)
    assert result.classification == "unclear" and result.reason == "synthetic_timing"


def test_display_geometry_cannot_drive_classification():
    raw = supported([i / 6 for i in range(40)])
    fake_level_display = display_contour(supported([0] * 40))
    measured = classify_contour(fake_level_display, 0, 0.4, raw=raw)
    assert measured.classification == "2-like"


@pytest.mark.parametrize("base_hz", [90, 180, 320])
def test_region_selection_is_independent_of_speaker_pitch(base_hz):
    raw = weak_attack([0] * 40)
    scale = base_hz / raw[3]["f0_hz"]
    for p in raw:
        p["f0_hz"] *= scale
        if p["comparison_f0_hz"]:
            p["comparison_f0_hz"] *= scale
    region = select_tone_evidence(raw, 0, 0.43)
    assert region.onset_frames == 3 and region.start == 0.03

"""Synthetic invariants and separately identified persisted human regressions."""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import pytest
from test_tone_evidence_region import supported

from benma_api.pronunciation.contours import classify_contour, display_contour
from benma_api.pronunciation.evidence_region import select_tone_evidence


def classify(raw):
    return classify_contour(display_contour(raw), 0, len(raw) * 0.01, raw=raw)


def broad(bins):
    return supported([value for value in bins for _ in range(8)])


@pytest.mark.parametrize(
    "bins,label,confidence",
    [
        ([3, 1, -2, 0, 3], "3-like", "moderate"),
        ([1.2, 0.3, 0, 0.5, 2], "3-like", "low"),
        ([2, 0.5, 0, 0.3, 1.2], "3-like", "low"),  # final below onset
        ([0, -0.4, 1, 2, 4], "2-like", "moderate"),
        ([0, 1, 2, 3, 4], "2-like", "moderate"),
        ([4, 3, 2, 1, 0], "4-like", "moderate"),
        ([0.1, -0.1, 0, 0.1, -0.1], "1-like", "moderate"),
        ([2, -1, 2, -1, 2], "unclear", "low"),
        ([1.8, 0.4, 0, 0.1, 0.3], "unclear", "low"),
        ([1.2, 0, 0.2, 0.5, 2], "unclear", "low"),  # early sag, weak net rise
        ([0, -0.5, -0.6, 1, 4], "2-like", "moderate"),  # centered tiny sag
    ],
)
def test_synthetic_shape_separation(bins, label, confidence):
    result = classify(broad(bins))
    assert (result.classification, result.confidence) == (label, confidence)


def gapped(direction=-1):
    # Stable motion on both sides, with a larger same-direction step while F0
    # is absent. These are synthetic observations, not interpolated gap frames.
    values = [direction * i * 0.1 for i in range(15)]
    values += [0, 0]
    values += [direction * (4 + i * 0.1) for i in range(23)]
    raw = supported(values)
    for p in raw[15:17]:
        p.update(f0_hz=None, comparison_f0_hz=None, voicing_probability=0)
    return raw


@pytest.mark.parametrize("direction,label", [(-1, "4-like"), (1, "2-like")])
def test_synthetic_discontinuous_short_gap_uses_observed_segments(direction, label):
    raw = gapped(direction)
    before = copy.deepcopy(raw)
    result = classify(raw)
    assert (result.classification, result.confidence, result.reason) == (
        label,
        "low",
        "coherent_short_gap",
    )
    assert result.features["discontinuous_gap_count"] == 1
    assert result.features["retained_after_filter_count"] == 38
    assert len(display_contour(raw).segments) == 2
    assert raw == before


@pytest.mark.parametrize("shape,label", [("level", "1-like"), ("valley", "3-like")])
def test_synthetic_small_gap_preserves_observable_structure(shape, label):
    raw = supported([0 if shape == "level" else abs(i - 20) * 0.2 for i in range(41)])
    for p in raw[10:12]:
        p.update(f0_hz=None, comparison_f0_hz=None, voicing_probability=0)
    assert classify(raw).classification == label


@pytest.mark.parametrize(
    "fault",
    [
        "long",
        "multiple",
        "reverse_step",
        "reverse_limb",
        "octave",
        "contamination",
        "low_evidence",
        "weak_flank",
        "unknown_strength",
        "missing_comparison",
        "disagreement",
        "noisy_limb",
    ],
)
def test_synthetic_gap_exception_cannot_rescue_bad_evidence(fault):
    raw = gapped()
    if fault == "long":
        for p in raw[17:]:
            p["timestamp_seconds"] += 0.1
    elif fault == "multiple":
        raw[28]["f0_hz"] = None
    elif fault == "reverse_step":
        for p in raw[17:]:
            p["f0_hz"] *= 2 ** (6 / 12)
            p["comparison_f0_hz"] = p["f0_hz"]
    elif fault == "reverse_limb":
        values = [p["f0_hz"] for p in raw[17:]][::-1]
        for p, hz in zip(raw[17:], values, strict=True):
            p.update(f0_hz=hz, comparison_f0_hz=hz)
    elif fault == "octave":
        for p in raw[17:]:
            p["f0_hz"] /= 2
            p["comparison_f0_hz"] = p["f0_hz"]
    elif fault == "contamination":
        for p in raw[20:30]:
            p.update(quality_usable=False, low_frequency_contaminated=True)
    elif fault == "low_evidence":
        raw = raw[12:22]
        for i, p in enumerate(raw):
            p["timestamp_seconds"] = i * 0.01
    elif fault == "weak_flank":
        raw[17]["voicing_probability"] = 0.5
    elif fault == "unknown_strength":
        raw[17]["voicing_probability"] = None
    elif fault == "missing_comparison":
        raw[17].pop("comparison_f0_hz")
    elif fault == "disagreement":
        raw[17]["comparison_f0_hz"] *= 2
    elif fault == "noisy_limb":
        for i, p in enumerate(raw[20:]):
            p["f0_hz"] *= 2 ** ((3 * math.sin(i * 2)) / 12)
    assert classify(raw).classification == "unclear"


def test_synthetic_tracker_failure_cannot_become_shallow_valley():
    raw = broad([1.2, 0.3, 0, 0.5, 2])
    for i in [8, 15, 22]:
        raw[i]["f0_hz"] /= 2
    assert classify(raw).classification == "unclear"


def test_persisted_latest_phone_results_and_raw_display_independence():
    rows = json.loads((Path(__file__).parent / "fixtures/final_narrow_pitch.json").read_text())
    expected = [
        ("1-like", "moderate"),
        ("3-like", "low"),
        ("unclear", "low"),
        ("4-like", "low"),
        ("1-like", "moderate"),
    ]
    for row, wanted in zip(rows, expected, strict=True):
        raw = row["raw"]
        original = copy.deepcopy(raw)
        display = display_contour(raw)
        kwargs = dict(raw=raw, timing_reliable=row["timing_reliable"])
        result = classify_contour(display, row["start"], row["end"], **kwargs)
        assert (result.classification, result.confidence) == wanted
        # Even a fabricated continuous level drawing cannot change grading.
        altered = display_contour(supported([0] * 160))
        assert classify_contour(altered, row["start"], row["end"], **kwargs) == result
        assert raw == original


def test_target_metadata_does_not_enter_selection_or_classification():
    raw = broad([1.2, 0.3, 0, 0.5, 2])
    outcomes = []
    for expected in [3, 2, 4, 1, 0]:
        tagged = [{**p, "expected_surface_tone": expected} for p in raw]
        outcomes.append(
            (select_tone_evidence(tagged, 0, 0.4), display_contour(tagged), classify(tagged))
        )
    assert all(outcome == outcomes[0] for outcome in outcomes)
    assert outcomes[0][-1].classification == "3-like"


@pytest.mark.parametrize("sample_index", [1, 3])
def test_api_target_revision_preserves_acoustic_evidence(
    client, auth_header, uploaded_utterance, monkeypatch, sample_index
):
    from benma_api.pronunciation.acoustics import AutocorrelationAcousticAnalyzer
    from benma_api.speech.contracts import AssessmentEvidence, AssessmentProviderResponse
    from benma_api.speech.providers.replay import ReplayPronunciationProvider

    row = json.loads((Path(__file__).parent / "fixtures/final_narrow_pitch.json").read_text())[
        sample_index
    ]
    raw = row["raw"]
    monkeypatch.setattr(
        AutocorrelationAcousticAnalyzer,
        "analyze",
        lambda *_: {
            "f0": raw,
            "mobile_f0": raw,
            "duration_seconds": row["end"],
            "recording_quality": {"status": "usable", "issues": []},
        },
    )
    # Test-only simulated live timing; no external provider is contacted.
    monkeypatch.setattr(ReplayPronunciationProvider, "provider_name", "test-live")
    monkeypatch.setattr(
        ReplayPronunciationProvider,
        "assess",
        lambda *_: AssessmentProviderResponse(
            evidence=AssessmentEvidence(
                evidence_status="live_provider",
                syllables=[
                    {
                        "text": row["target"],
                        "timing": {"start_seconds": row["start"], "end_seconds": row["end"]},
                    }
                ],
            ),
            raw_payload={"fixture": True},
        ),
    )
    original = client.post(
        "/v1/pronunciation-targets", headers=auth_header, json={"text": row["target"]}
    ).json()
    revised = client.post(
        f"/v1/pronunciation-targets/{original['id']}/pinyin-corrections",
        headers=auth_header,
        json={"pinyin": "ma2"},
    ).json()
    results = []
    for target in [original, revised]:
        attempt = client.post(
            "/v1/pronunciation-attempts",
            headers=auth_header,
            json={"utterance_id": uploaded_utterance["id"], "target_id": target["id"]},
        ).json()
        response = client.post(
            f"/v1/pronunciation-attempts/{attempt['id']}/analyze", headers=auth_header, json={}
        )
        assert response.status_code == 200
        results.append(response.json())
    a, b = [r["syllables"][0] for r in results]
    assert a["expected_surface_tone"] != b["expected_surface_tone"] == 2
    assert a["observed_contour"] == b["observed_contour"]
    assert a["observed_contour"]["classification"] == ("3-like" if sample_index == 1 else "4-like")
    assert a["display_contour"] == b["display_contour"]
    assert results[0]["display_contour"] == display_contour(raw).model_dump()
    assert (
        results[0]["acoustic"]["normalized_result"]["f0"]
        == results[1]["acoustic"]["normalized_result"]["f0"]
    )


def test_display_summary_is_exact_medians_without_grading_feedback():
    import statistics

    raw = supported([2, 1, 0, -1, -2] * 8)
    before = json.dumps(raw)
    measured = display_contour(raw)
    result = classify(raw)
    points = [p for segment in measured.segments for p in segment]
    for i in range(5):
        group = points[i * len(points) // 5 : (i + 1) * len(points) // 5]
        assert result.features[f"bin_{i + 1}_st"] == round(
            statistics.median(p.normalized_semitones for p in group), 4
        )
        assert result.features[f"bin_{i + 1}_seconds"] == round(
            statistics.median(p.timestamp_seconds for p in group), 4
        )
    assert classify_contour(None, 0, len(raw) * 0.01, raw=raw) == result
    assert json.dumps(raw) == before

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from benma_api.pronunciation.acoustics import reject_terminal_octave_ambiguity
from benma_api.pronunciation.contours import classify_contour, display_contour
from benma_api.pronunciation.timing import resolve_target_timing

FIXTURE = Path(__file__).parent / "fixtures/phone_upstream_evidence.json"


def resolve(row, acoustic=None):
    return resolve_target_timing(
        row["alignment"],
        status="succeeded",
        characters=[row["text"]],
        readings=row["readings"],
        acoustic=acoustic or row["acoustic"],
    )


def test_real_phone_timing_reaches_contours_without_source_metadata():
    for row in json.loads(FIXTURE.read_text()):
        snapshot = copy.deepcopy(row)
        resolution = resolve(row)
        assert resolution["accepted"]
        unit = row["alignment"]["units"][0]
        raw = row["acoustic"]["f0"]
        result = classify_contour(
            display_contour(raw), unit["start_seconds"], unit["end_seconds"], raw=raw
        )
        assert result.reason != "timing_unavailable"
        assert result.features["raw_voiced_frames"] > 0
        if row["id"].startswith("2ce6"):
            assert result.classification == "1-like"
        if row["id"].startswith("12df"):
            assert result.classification == "2-like"
        if row["id"].startswith(("1243", "a624")):
            assert resolution["reason"] == "acoustically_supported_recording_padding"
            unit.pop("source", None)
            assert resolve(row)["accepted"]  # Live row/target identity carries provenance.
        else:
            assert row == snapshot


@pytest.mark.parametrize(
    "failure",
    ["synthetic", "identity", "overlap", "nan", "missing", "outside", "unknown_rejection"],
)
def test_padding_exception_does_not_weaken_other_gates(failure):
    row = json.loads(FIXTURE.read_text())[1]
    if failure == "synthetic":
        row["alignment"]["evidence_status"] = "synthetic_replay"
    elif failure == "identity":
        row["alignment"]["units"][0]["label"] = "麻"
    elif failure == "overlap":
        row["alignment"]["units"] *= 2
    elif failure == "nan":
        row["alignment"]["units"][0]["start_seconds"] = float("nan")
    elif failure == "missing":
        row["acoustic"] = {"duration_seconds": 2.2}
    elif failure == "outside":
        row["acoustic"]["f0"] += [
            {**p, "timestamp_seconds": p["timestamp_seconds"] - 1}
            for p in row["acoustic"]["f0"]
            if p["f0_hz"]
        ]
    else:
        row["alignment"]["quality"]["issues"].append("future_integrity_failure")
    assert not resolve(row)["accepted"]


def test_terminal_octave_rejection_is_bounded_and_raw_is_preserved():
    row = json.loads(FIXTURE.read_text())[2]
    raw = row["acoustic"]["f0"]
    before = copy.deepcopy(raw)
    reject_terminal_octave_ambiguity(raw, row["acoustic"]["energy_gate"]["threshold_rms"])
    rejected = [p for p in raw if p.get("selection_reason", "").startswith("terminal_octave")]
    assert len(rejected) == 6
    assert rejected[-1]["timestamp_seconds"] - rejected[0]["timestamp_seconds"] <= 0.08
    assert [p["f0_hz"] for p in raw] == [p["f0_hz"] for p in before]
    assert all(p["selected_f0_hz"] is None for p in rejected)
    assert all(
        p["pitch_candidates"] == q["pitch_candidates"] for p, q in zip(raw, before, strict=True)
    )
    unit = row["alignment"]["units"][0]
    result = classify_contour(
        display_contour(raw), unit["start_seconds"], unit["end_seconds"], raw=raw
    )
    assert result.classification == "unclear"  # No label rescue from unsupported octaves.
    assert result.features["bin_5_st"] > -5
    once = copy.deepcopy(raw)
    reject_terminal_octave_ambiguity(raw, row["acoustic"]["energy_gate"]["threshold_rms"])
    assert raw == once


@pytest.mark.parametrize(
    "change", ["strong_alternative", "interior", "missing_candidates", "no_energy_decay"]
)
def test_terminal_rejection_requires_acoustic_support(change):
    row = json.loads(FIXTURE.read_text())[2]
    raw = row["acoustic"]["f0"]
    if change == "strong_alternative":
        p = next(p for p in raw if p["timestamp_seconds"] == 1.0943)
        p["pitch_candidates"].append({"frequency_hz": p["f0_hz"] * 2, "strength": 0.8})
    elif change == "interior":
        raw[-1].update(f0_hz=110, quality_usable=True)
    elif change == "missing_candidates":
        for p in raw:
            p.pop("pitch_candidates", None)
    else:
        for p in raw:
            p["energy_rms"] = 0.1
    before = copy.deepcopy(raw)
    reject_terminal_octave_ambiguity(raw, row["acoustic"]["energy_gate"]["threshold_rms"])
    assert raw == before


@pytest.mark.parametrize("warmup_first", [True, False])
def test_api_reconciles_padded_timing_and_reuses_exact_runs(
    client,
    auth_header,
    monkeypatch,
    warmup_first,
):
    from conftest import wav_bytes

    from benma_api.pronunciation.acoustics import AutocorrelationAcousticAnalyzer
    from benma_api.pronunciation.alignment import AlignmentResponse, ReplayAligner

    row = json.loads(FIXTURE.read_text())[1]
    calls = []

    def analyze(*_):
        calls.append("acoustic")
        return {
            **row["acoustic"],
            "mobile_f0": row["acoustic"]["f0"],
            "recording_quality": {"status": "usable", "issues": []},
        }

    monkeypatch.setattr(AutocorrelationAcousticAnalyzer, "analyze", analyze)
    monkeypatch.setattr(
        ReplayAligner,
        "align",
        lambda *_: AlignmentResponse(
            units=row["alignment"]["units"],
            raw_result={},
            evidence_status="live_provider",
        ),
    )
    uid = client.post(
        "/v1/utterances",
        headers=auth_header,
        files={"file": ("padding.wav", wav_bytes(2.2059), "audio/wav")},
    ).json()["id"]
    warmup = (
        client.post(f"/v1/utterances/{uid}/acoustics", headers=auth_header).json()
        if warmup_first
        else None
    )
    target = client.post(
        "/v1/pronunciation-targets", headers=auth_header, json={"text": "嘛"}
    ).json()
    attempt = client.post(
        "/v1/pronunciation-attempts",
        headers=auth_header,
        json={"utterance_id": uid, "target_id": target["id"]},
    ).json()
    path = f"/v1/pronunciation-attempts/{attempt['id']}"
    before = client.get(path + "/result", headers=auth_header).json()
    assert before["syllables"][0]["observed_contour"]["reason"] == "timing_unavailable"
    first = client.post(path + "/analyze", headers=auth_header, json={}).json()
    again = client.post(path + "/analyze", headers=auth_header, json={}).json()
    assert calls == ["acoustic"]
    if warmup:
        assert first["acoustic"]["id"] == warmup["id"]
    for name in ["acoustic", "alignment", "assessment", "interpretation"]:
        assert first[name]["id"] == again[name]["id"]
    resolution = first["overall_evidence"]["timing_resolution"]
    assert resolution["accepted"]
    assert resolution["reason"] == "acoustically_supported_recording_padding"
    assert first["syllables"][0]["observed_contour"]["features"]["raw_voiced_frames"] > 0
    assert first["syllables"][0]["observed_contour"] == again["syllables"][0]["observed_contour"]
    assert first["alignment"]["normalized_result"]["quality"]["issues"] == [
        "excessive_unaligned_audio"
    ]

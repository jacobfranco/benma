"""Signal and information-boundary tests, with synthetic waveforms (not pronunciation gold)."""

import dataclasses
import json

import numpy as np
import pytest

from benchmark.pronunciation_v2 import phonetic_evidence as pe
from benchmark.pronunciation_v2.phonetic_evidence import load_manifest, verify_seal
from benchmark.pronunciation_v2.phonetic_packet import build_packet
from benchmark.pronunciation_v2.phonetic_prepare import control_candidates


def wave():
    t = np.arange(16000) / 16000
    return (0.2 * np.sin(2 * np.pi * 170 * t)).astype(np.float32)


def frames(start=0.205, n=15, voiced=True):
    return tuple(
        pe.SavedFrame(
            start + i / 100,
            170 if voiced else None,
            170 if voiced else None,
            True,
            0.8 if voiced else 0.0,
            0.1,
        )
        for i in range(n)
    )


def test_target_cannot_enter_extractor():
    with pytest.raises(TypeError):
        pe.extract_observed(wave(), pe.Span(100, 500), intended_text="target")
    with pytest.raises(TypeError):
        pe.Span(start_ms=100, end_ms=500, pinyin="x")
    with pytest.raises(TypeError):
        pe.SavedFrame(**dataclasses.asdict(frames()[0]), phone="reference")
    with pytest.raises(TypeError):
        pe.extract_observed(wave(), {"start_ms": 100, "end_ms": 500, "target": "x"})


def test_deterministic_target_invariance():
    record = {"target": "one", "span": pe.Span(100, 500), "audio": wave()}
    first = pe.extract_observed(record["audio"], record["span"], frames())
    record["target"] = "different"
    second = pe.extract_observed(record["audio"], record["span"], frames())
    assert first == second
    assert first["quality_flags"] == second["quality_flags"]
    assert "target" not in json.dumps(first)


@pytest.mark.parametrize(
    "span,flag",
    [
        (pe.Span(-1, 50), "invalid_span"),
        (pe.Span(50, 50), "invalid_span"),
        (pe.Span(50, 40), "invalid_span"),
        (pe.Span(float("nan"), 40), "invalid_span"),
        (pe.Span(0, 1001), "span_outside_audio"),
        (pe.Span(100, 110), "insufficient_duration"),
    ],
)
def test_span_abstention(span, flag):
    result = pe.extract_observed(wave(), span)
    assert result["status"] == "abstained"
    assert flag in result["quality_flags"]
    assert result["formants"] is None


@pytest.mark.parametrize("samples", [np.zeros(16000), wave()])
def test_missing_voicing_never_fabricated(samples):
    result = pe.extract_observed(samples, pe.Span(100, 500), frames(voiced=False))
    assert result["pitch"]["selected_hz"] is None
    assert result["formants"]["summary_hz"] is None
    assert result["analysis_windows"] == []
    assert result["onset"]["status"] == "unresolved"


def test_saved_f0_exact_reuse_and_quality_gate(monkeypatch):
    saved = (
        pe.SavedFrame(0.2, 201, 209, True, 0.7, 0.1),
        pe.SavedFrame(0.21, 202, 212, False, 0.7, 0.1),
        pe.SavedFrame(0.22, None, None, True, 0, 0.1),
        pe.SavedFrame(0.5, 333, 333, True, 0.7, 0.1),
    )

    def fail(*a, **kw):
        pytest.fail("No formants without supported candidate")

    monkeypatch.setattr(pe, "_burg_rows", fail)
    result = pe.extract_observed(wave(), pe.Span(200, 500), saved)
    p = result["pitch"]
    assert p["frame_count"] == 3  # End-exclusive slicing.
    assert p["usable_frame_count"] == 1
    assert p["selected_hz"]["median"] == 209  # Never raw 201, unstable 212, or recomputed 170.
    assert p["tracker_instability_frames"] == 1
    assert p["frames"][0]["timestamp_seconds"] == 0
    assert p["frames"][1]["selected_f0_hz"] == 212


def test_windows_follow_signal_not_equal_subdivision():
    r = pe.extract_observed(wave(), pe.Span(100, 600), frames(start=0.285, n=12))
    nucleus = r["analysis_windows"][0]
    assert nucleus["start_ms"] == pytest.approx(180)
    assert nucleus["end_ms"] == pytest.approx(300)
    assert all(
        w["semantics"] == "analysis_window_not_phoneme_boundary" for w in r["analysis_windows"]
    )
    no_run = tuple(
        dataclasses.replace(p, quality_usable=(i % 4 != 0)) for i, p in enumerate(frames())
    )
    assert pe.extract_observed(wave(), pe.Span(100, 600), no_run)["analysis_windows"] == []


def test_formant_failure_remains_missing(monkeypatch):
    def fail(*args):
        raise RuntimeError("Burg failed")

    monkeypatch.setattr(pe, "_burg_rows", fail)
    result = pe.extract_observed(wave(), pe.Span(100, 500), frames())
    assert result["formants"]["status"] == "extraction_failed"
    assert result["formants"]["summary_hz"] is None


@pytest.mark.parametrize(
    "mode,expected",
    [
        ("stable", "feasible_numeric_track"),
        ("outlier", "quality_abstention"),
        ("jump", "quality_abstention"),
    ],
)
def test_formant_guards_and_full_support(monkeypatch, mode, expected):
    def burg(crop, centers):
        assert min(centers) >= 0.125  # Candidate starts 100 ms into crop; full 50 ms support.
        assert max(centers) <= 0.225 + 1e-6
        rows = []
        for i, t in enumerate(centers):
            f = [500, 1500, 2500]
            if mode == "outlier":
                f = [50, 1500, 2500]
            if mode == "jump" and i % 2:
                f = [900, 1500, 2500]
            rows.append({"time_ms": t * 1000, "hz": f, "bandwidth_hz": [100, 100, 100]})
        return rows

    monkeypatch.setattr(pe, "_burg_rows", burg)
    result = pe.extract_observed(wave(), pe.Span(100, 500), frames())
    assert result["formants"]["status"] == expected
    assert (result["formants"]["summary_hz"] is not None) == (mode == "stable")


def manifest(tmp_path):
    audio = tmp_path / "source.wav"
    audio.write_bytes(b"hash-only-stub")
    value = {
        "version": 1,
        "regions": [
            {
                "id": "R01",
                "audio_path": str(audio),
                "audio_sha256": pe.sha(audio),
                "span": {"start_ms": 100, "end_ms": 500},
                "saved_frames": [dataclasses.asdict(p) for p in frames()],
            }
        ],
    }
    path = tmp_path / "manifest.json"
    pe.dump(path, value)
    return path, value


@pytest.mark.parametrize("where", ["top", "region", "span", "frame"])
def test_manifest_forbids_leakage(tmp_path, where):
    path, value = manifest(tmp_path)
    region = value["regions"][0]
    containers = {
        "top": value,
        "region": region,
        "span": region["span"],
        "frame": region["saved_frames"][0],
    }
    containers[where]["intended_text"] = "secret"
    pe.dump(path, value)
    with pytest.raises((ValueError, TypeError)):
        load_manifest(path)


def test_blind_packet_and_key_separation(tmp_path, monkeypatch):
    from benchmark.pronunciation_v2 import phonetic_packet as pp

    path, _ = manifest(tmp_path)
    pe.dump(tmp_path / "unblinding-key.json", {"character": "secret", "score": 100})
    monkeypatch.setattr(pp, "decode", lambda path: wave())
    packet = tmp_path / "blind"
    build_packet(path, packet)
    assert verify_seal(packet)
    for file in packet.rglob("*"):
        if file.is_file() and file.suffix != ".wav":
            text = file.read_text()
            for forbidden in (
                "secret",
                "intended_text",
                "pinyin",
                "AccuracyScore",
                "source.wav",
                "S13",
                "reference_phone",
            ):
                assert forbidden not in text
    assert not (packet / "unblinding-key.json").exists()
    (packet / "observations.md").write_text("tampered")
    with pytest.raises(ValueError, match="changed"):
        verify_seal(packet)


def test_controls_ignore_reference_scores():
    def unit(uid, n, score):
        return {
            "unit_id": uid,
            "timing": {"start_ms": 0, "end_ms": 500},
            "score": score,
            "reading": "forbidden",
            "pitch": {
                "usable_frame_count": n,
                "frame_count": 10,
                "frames": [{"energy_rms": 0.1, "quality_usable": True}],
            },
        }

    records = {
        s: {"alignment": {"issues": []}, "units": [unit("u0", 8, 0), unit("u1", 6, 100)]}
        for s in ("S02", "S03")
    }
    before = control_candidates(records)
    records["S02"]["units"][0]["score"] = 100
    assert control_candidates(records) == before
    assert before[0][:2] == ("S02", "u0")


def test_spectrum_tracks_frequency_without_sound_label():
    low = pe.extract_observed(wave(), pe.Span(100, 500))
    t = np.arange(16000) / 16000
    high = pe.extract_observed(0.2 * np.sin(2 * np.pi * 5000 * t), pe.Span(100, 500))
    assert low["spectrum"]["centroid_hz"]["median"] == pytest.approx(170, abs=5)
    assert high["spectrum"]["centroid_hz"]["median"] == pytest.approx(5000, abs=5)
    assert high["spectrum"]["high_frequency_fraction"]["median"] > 0.99
    assert low["spectrum"]["high_frequency_fraction"]["median"] < 0.01
    assert low["analysis_windows"] == high["analysis_windows"] == []


def test_order_and_nonfinite_frame_guards():
    with pytest.raises(ValueError, match="ordered"):
        pe.extract_observed(wave(), pe.Span(100, 500), frames()[::-1])
    with pytest.raises(ValueError, match="Nonfinite"):
        dataclasses.replace(frames()[0], selected_f0_hz=float("nan"))
    samples = wave()
    samples[123] = float("nan")
    assert pe.extract_observed(samples, pe.Span(100, 500))["quality_flags"] == ["invalid_audio"]


def test_short_supported_run_does_not_force_formants():
    result = pe.extract_observed(wave(), pe.Span(100, 190), frames(start=0.145, n=5))
    assert result["analysis_windows"]
    assert result["formants"]["summary_hz"] is None
    assert result["formants"]["usable_frames"] < 3

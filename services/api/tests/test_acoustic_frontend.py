from __future__ import annotations

import copy
import math
import wave

import numpy as np
import pytest
from test_readings_contours import raw_contour

from benma_api.pronunciation.acoustics import PraatAcousticAnalyzer
from benma_api.pronunciation.contours import classify_contour, display_contour


@pytest.mark.parametrize(
    "variant", ["clean", "tap", "broadband", "hum", "onset", "gap", "hum_only", "tap_only"]
)
def test_periodic_speech_not_arbitrary_energy_drives_pitch(tmp_path, variant):
    rate = 16000
    t = np.arange(rate) / rate
    phase = 2 * np.pi * 180 * t
    envelope = ((t >= 0.2) & (t < 0.8)).astype(float)
    signal = 0.15 * envelope * (np.sin(phase) + 0.3 * np.sin(2 * phase) + 0.15 * np.sin(3 * phase))
    if variant == "tap":
        signal[8000] += 0.7
    elif variant == "broadband":
        signal[7900:8100] += np.random.default_rng(4).normal(0, 0.15, 200)
    elif variant == "hum":
        signal += 0.012 * np.sin(2 * np.pi * 60 * t)
    elif variant == "onset":
        signal[(t >= 0.2) & (t < 0.25)] *= 0.15
    elif variant == "gap":
        signal[(t >= 0.49) & (t < 0.51)] = 0
    elif variant == "hum_only":
        signal = 0.02 * np.sin(2 * np.pi * 60 * t)
    elif variant == "tap_only":
        signal[:] = 0
        signal[8000] = 0.8
    path = tmp_path / (variant + ".wav")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes((np.clip(signal, -1, 1) * 32767).astype("<i2").tobytes())
    result = PraatAcousticAnalyzer().analyze(path)
    raw = result["f0"]
    display = display_contour(raw)
    measured = classify_contour(display, 0.2, 0.8, raw=raw)
    if variant in {"hum_only", "tap_only"}:
        assert measured.classification == "unclear"
        assert not display.segments
    else:
        assert measured.classification == "1-like", (variant, measured)
        assert all(abs(p.normalized_semitones) < 1 for seg in display.segments for p in seg)
    assert result["selection"]["repaired_frame_count"] == 0


@pytest.mark.parametrize(
    "gap_frames,step,expected", [(2, 0, "1-like"), (12, 0, "unclear"), (2, 4, "unclear")]
)
def test_dropout_is_missing_observation_with_continuity_required(gap_frames, step, expected):
    raw = raw_contour([0] * 25 + [step] * 25)
    for p in raw[23 : 23 + gap_frames]:
        p["f0_hz"] = None
    snapshot = copy.deepcopy(raw)
    display = display_contour(raw)
    measured = classify_contour(display, 0, 0.5, raw=raw)
    assert measured.classification == expected
    assert len(display.segments) == 2
    assert raw == snapshot
    missing = {p["timestamp_seconds"] for p in raw if p["f0_hz"] is None}
    assert not missing.intersection(p.timestamp_seconds for s in display.segments for p in s)


def test_repeated_octave_chaos_is_not_repaired():
    raw = raw_contour([0 if i % 4 else -12 for i in range(50)])
    measured = classify_contour(display_contour(raw), 0, 0.5, raw=raw)
    assert measured.classification == "unclear"
    assert measured.features["tracker_instability_rejected"]


@pytest.mark.parametrize(
    "values,label",
    [
        ([0] * 50, "1-like"),
        ([i / 8 for i in range(50)], "2-like"),
        ([abs(i - 25) / 5 for i in range(50)], "3-like"),
        ([-i / 8 for i in range(50)], "4-like"),
    ],
)
def test_shape_controls_unchanged(values, label):
    raw = raw_contour(values)
    result = classify_contour(display_contour(raw), 0, 0.5, raw=raw)
    assert result.classification == label
    assert math.isfinite(result.features["change_st"])

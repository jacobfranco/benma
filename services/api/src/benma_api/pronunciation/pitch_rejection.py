"""Audio-only rejection proofs. Never replace tracker F0 or consult text/timing."""

from __future__ import annotations

import math
import statistics
from itertools import pairwise
from typing import Any

BRANCH_REASON = "candidate_supported_ambiguous_branch"
BACKGROUND_REASON = "persistent_background_periodicity"
REJECTION_VERSION = "candidate-branch-background-v1"


def _distance(a: float, b: float) -> float:
    return abs(12 * math.log2(a / b))


def reject_ambiguous_branches(points: list[dict[str, Any]]) -> int:
    """Keep a >=120 ms coherent primary; reject only a <=70 ms harmonic branch.

    Entire raw islands are examined, including energy-gated frames and frames
    outside any aligned syllable. A branch cannot be shortened by a text boundary.
    Alternatives certify ambiguity, NOT the pitch to substitute. No extrapolation.
    """
    islands: list[list[dict[str, Any]]] = []
    for p in points:
        if not p.get("tracker_f0_hz"):
            continue
        if not islands or p["timestamp_seconds"] - islands[-1][-1]["timestamp_seconds"] > 0.015:
            islands.append([])
        islands[-1].append(p)
    rejected = 0
    for island_index, (primary, branch) in enumerate(pairwise(islands)):
        # A missing interval is required; adjacent octave switches remain unsafe.
        gap = branch[0]["timestamp_seconds"] - primary[-1]["timestamp_seconds"]
        if not 0.015 < gap <= 0.05 + 1e-8:
            continue
        if (
            len(primary) < 12
            or primary[-1]["timestamp_seconds"] - primary[0]["timestamp_seconds"] < 0.11 - 1e-8
            or not 2 <= len(branch) <= 7
            or len(branch) > len(primary) / 2
            or branch[-1]["timestamp_seconds"] - branch[0]["timestamp_seconds"] > 0.06 + 1e-8
        ):
            continue
        hz = [p["tracker_f0_hz"] for p in primary]
        if not 6 < _distance(hz[-1], branch[0]["tracker_f0_hz"]) < 15:
            continue
        # Repeated nearby switches are chaos, not one isolated ambiguous ending.
        neighbours = []
        if island_index:
            neighbours.append((islands[island_index - 1][-1], primary[0]))
        if island_index + 2 < len(islands):
            neighbours.append((branch[-1], islands[island_index + 2][0]))
        if any(
            b["timestamp_seconds"] - a["timestamp_seconds"] <= 0.05 + 1e-8
            and _distance(a["tracker_f0_hz"], b["tracker_f0_hz"]) > 6
            for a, b in neighbours
        ):
            continue
        if any(not p.get("quality_usable", True) or not p.get("selected_f0_hz") for p in primary):
            continue
        if max(_distance(a, b) for a, b in pairwise(hz)) > 1.5:
            continue
        if statistics.median(p.get("voicing_probability", 0) for p in primary) < 0.75:
            continue
        # Filter agreement and a preferred selected path throughout the primary.
        if any(
            not p.get("comparison_f0_hz")
            or _distance(p["comparison_f0_hz"], p["tracker_f0_hz"]) > 1
            for p in primary
        ):
            continue
        advantages = [
            p.get("voicing_probability", 0)
            - max(
                (
                    c["strength"]
                    for c in p.get("pitch_candidates", [])
                    if _distance(c["frequency_hz"], p["tracker_f0_hz"]) > 6
                ),
                default=0,
            )
            for p in primary
        ]
        if min(advantages) < 0 or statistics.median(advantages) < 0.05:
            continue
        alternatives = []
        for p in branch:
            raw = p["tracker_f0_hz"]
            matches = [
                c
                for c in p.get("pitch_candidates", [])
                if abs(_distance(c["frequency_hz"], raw) - 12) <= 1.5
                and min(hz) / 2 ** (1 / 12) <= c["frequency_hz"] <= max(hz) * 2 ** (1 / 12)
                and c["strength"] >= 0.4
                and c["strength"] >= 0.75 * p.get("voicing_probability", 1)
            ]
            if not matches or _distance(raw, branch[0]["tracker_f0_hz"]) > 2:
                break
            alternatives.append(max(matches, key=lambda c: c["strength"]))
        if len(alternatives) != len(branch) or sum(c["strength"] >= 0.5 for c in alternatives) < 2:
            continue
        for p in branch:
            # Existing environmental rejection retains its more specific reason.
            if not p.get("quality_usable", True):
                continue
            p["quality_usable"] = False
            p["selected_f0_hz"] = None
            p["selection_reason"] = BRANCH_REASON
            rejected += 1
    return rejected


def background_periodicity(values: Any, rate: float) -> dict[str, Any]:
    """Measure persistence in quiet high-band windows, independent of tracker F0.

    200 ms Hann spectra, 50 ms hop. Require speech/background contrast plus
    >=500 ms of quiet, low-band-dominated support spread over >=60% of recording.
    A low voice confined to speech and transient rumble cannot establish a bed.
    """
    import numpy as np

    width, hop = round(rate * 0.2), round(rate * 0.05)
    windows = []
    for start in range(0, len(values) - width + 1, hop):
        frame = values[start : start + width]
        power = np.abs(np.fft.rfft((frame - frame.mean()) * np.hanning(width))) ** 2
        frequencies = np.fft.rfftfreq(width, 1 / rate)
        low = (frequencies >= 40) & (frequencies <= 80)
        total = float(power[(frequencies >= 40) & (frequencies <= 4000)].sum())
        high = float(power[(frequencies >= 120) & (frequencies <= 4000)].sum())
        peak = float(frequencies[np.where(low)[0][np.argmax(power[low])]])
        windows.append(
            {
                "time": (start + width / 2) / rate,
                "high_power": high,
                "low_fraction": float(power[low].sum()) / max(1e-12, total),
                "peak_hz": peak,
            }
        )
    peak_high = max((w["high_power"] for w in windows), default=0)
    quiet = [w for w in windows if w["high_power"] <= 0.08 * peak_high]
    dominated = [w for w in quiet if w["low_fraction"] >= 0.65 and 50 <= w["peak_hz"] <= 75]
    duration = len(values) / rate
    span = dominated[-1]["time"] - dominated[0]["time"] if dominated else 0
    centers = [w["peak_hz"] for w in dominated]
    detected = (
        len(dominated) >= 10
        and len(dominated) >= 0.7 * len(quiet)
        and span >= max(0.6, duration * 0.6)
        and float(np.quantile(centers, 0.9) - np.quantile(centers, 0.1)) <= 15
    )
    return {
        "version": REJECTION_VERSION,
        "detected": bool(detected),
        "quiet_windows": len(quiet),
        "dominated_quiet_windows": len(dominated),
        "background_span_seconds": span,
        "peak_band_hz": [min(centers), max(centers)] if centers else None,
        "window_seconds": 0.2,
        "hop_seconds": 0.05,
        "windows": windows,
    }


def reject_background_pitch(points: list[dict[str, Any]], background: dict[str, Any]) -> int:
    if not background["detected"]:
        return 0
    rejected = 0
    for p in points:
        hz = p.get("tracker_f0_hz")
        # Lower local prominence is allowed ONLY after the recording-level proof.
        if hz and 45 <= hz < 80 and p.get("low_frequency_energy_fraction", 0) >= 0.45:
            p["quality_usable"] = False
            p["low_frequency_contaminated"] = True
            p["selected_f0_hz"] = None
            p["selection_reason"] = BACKGROUND_REASON
            rejected += 1
    return rejected

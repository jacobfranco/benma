"""Offline deterministic ownership experiment; never imported by Practice.

Only numeric Azure bounds, saved broadband RMS and waveform spectral features
are accepted. Thresholds are exploratory structural constants, not calibrated
operating points. A safe result is conditional on the supplied Azure ownership.
"""

import math
from itertools import pairwise

import numpy as np

MIN_SECONDS = 0.060
GAP_SECONDS = 0.020  # One frozen encoder stride, not a sweep over gap lengths.
DEEP_DB = -20.0  # Tenfold RMS depression relative to the weaker adjacent island.
FRICATION_ZCR = 0.25
FRICATION_HIGH_BAND = 0.25
DOMINANCE = 3.0
CANDIDATES = ("AZURE_SAFE_BASELINE", "CONTIGUOUS_SPEECH_SUPPORT", "GAP_AWARE_AZURE")
FEATURE_KEYS = ("time", "zcr", "high_band_fraction")


def energy_runs(whole, energy, threshold):
    runs = []
    for t, e in energy:
        if not whole[0] <= t < whole[1]:
            continue
        high = e >= threshold
        if not runs or runs[-1]["supported"] != high:
            runs.append({"supported": high, "centers": [], "rms": []})
        runs[-1]["centers"].append(t)
        runs[-1]["rms"].append(e)
    for run in runs:
        run["span"] = [
            max(whole[0], run["centers"][0] - 0.005),
            min(whole[1], run["centers"][-1] + 0.005),
        ]
        run["duration_ms"] = 1000 * (run["span"][1] - run["span"][0])
        run["median_rms"] = float(np.median(run["rms"]))
    return runs


def select_region(whole, previous, following, duration, energy, threshold, spectral, candidate):
    """No pitch, character, target, speaker, neutral flag, prediction or grade input.

    Deep separated substantial islands fail closed except a short, edge-attached,
    predominantly fricative onset followed by a >=3x dominant speech region.
    That exception preserves the complete onset, interruption and following body.
    """
    if candidate not in CANDIDATES:
        raise ValueError("unknown_candidate")
    result = {
        "ownership": "invalid",
        "representation": "abstain",
        "span": None,
        "reason": None,
        "gaps": [],
        "islands": [],
    }

    def reject(reason, ownership="invalid"):
        result.update(reason=reason, ownership=ownership)
        return result

    def numeric(x):
        return type(x) in (int, float) and math.isfinite(x)

    def valid_span(span):
        return (
            isinstance(span, (list, tuple))
            and len(span) == 2
            and all(numeric(v) for v in span)
            and 0 <= span[0] < span[1] <= duration
        )

    if not numeric(duration) or duration <= 0:
        return reject("invalid_duration")
    if not valid_span(whole) or any(
        s is not None and not valid_span(s) for s in (previous, following)
    ):
        return reject("invalid_azure_timing")
    a, b = whole
    if (previous is not None and previous[1] > a) or (following is not None and following[0] < b):
        return reject("overlapping_azure_ownership", "ambiguous")
    result["span"] = list(whole)
    if (
        not numeric(threshold)
        or threshold <= 0
        or not energy
        or any(len(p) != 2 or not all(numeric(v) for v in p) or p[1] < 0 for p in energy)
    ):
        return reject("invalid_energy")
    frames = [(t, e) for t, e in energy if a <= t < b]
    if (
        not frames
        or frames[0][0] - a > 0.015
        or b - frames[-1][0] > 0.015
        or any(not 0 < y[0] - x[0] <= 0.015 + 1e-9 for x, y in pairwise(frames))
    ):
        return reject("missing_energy_coverage")
    if not spectral or any(
        not all(k in r and numeric(r[k]) for k in FEATURE_KEYS)
        or not 0 <= r["zcr"] <= 1
        or not 0 <= r["high_band_fraction"] <= 1
        for r in spectral
    ):
        return reject("invalid_spectral_evidence")
    sf = [r for r in spectral if a <= r["time"] < b]
    if (
        not sf
        or sf[0]["time"] - a > 0.010
        or b - sf[-1]["time"] > 0.010
        or any(abs(y["time"] - x["time"] - 0.005) > 1e-8 for x, y in pairwise(sf))
    ):
        return reject("missing_spectral_coverage")
    runs = energy_runs(whole, frames, threshold)
    islands = [r for r in runs if r["supported"]]
    support = sum(r["duration_ms"] for r in islands) / 1000
    if b - a < MIN_SECONDS - 1e-9 or support < MIN_SECONDS - 1e-9:
        return reject("too_little_material", "safe" if islands else "invalid")
    for r in islands:
        r["frication_ms"] = 1000 * sum(
            max(0, min(r["span"][1], f["time"] + 0.0025) - max(r["span"][0], f["time"] - 0.0025))
            for f in spectral
            if r["span"][0] - 0.0025 < f["time"] < r["span"][1] + 0.0025
            and f["zcr"] >= FRICATION_ZCR
            and f["high_band_fraction"] >= FRICATION_HIGH_BAND
        )
        r["frication_fraction"] = r["frication_ms"] / r["duration_ms"]
        r["nonfricative_ms"] = r["duration_ms"] - r["frication_ms"]
    result["islands"] = [
        {
            k: r[k]
            for k in (
                "span",
                "duration_ms",
                "median_rms",
                "frication_ms",
                "frication_fraction",
                "nonfricative_ms",
            )
        }
        for r in islands
    ]
    if candidate == "CONTIGUOUS_SPEECH_SUPPORT":
        ranked = sorted(islands, key=lambda r: (-r["duration_ms"], r["span"][0]))
        if len(ranked) > 1 and ranked[1]["duration_ms"] >= 1000 * MIN_SECONDS - 1e-9:
            return reject("multiple_substantial_energy_islands", "ambiguous")
        result["span"] = ranked[0]["span"]
        if ranked[0]["duration_ms"] < 1000 * MIN_SECONDS - 1e-9:
            return reject("too_little_material", "safe")
    for j, gap in enumerate(runs):
        if gap["supported"] or j == 0 or j == len(runs) - 1:
            continue
        left, right = runs[j - 1], runs[j + 1]
        depth = float(
            20
            * np.log10(max(gap["median_rms"], 1e-12) / min(left["median_rms"], right["median_rms"]))
        )
        deep = gap["duration_ms"] >= 1000 * GAP_SECONDS - 1e-9 and depth <= DEEP_DB
        two_substantial = (
            min(left["duration_ms"], right["duration_ms"]) >= 1000 * MIN_SECONDS - 1e-9
        )
        onset = (
            j == 1
            and left["span"][0] - a <= 0.010 + 1e-9
            and left["frication_fraction"] >= 0.5
            and left["nonfricative_ms"] < 1000 * MIN_SECONDS
            and right["nonfricative_ms"] >= 1000 * MIN_SECONDS
            and right["duration_ms"] >= DOMINANCE * left["duration_ms"]
        )
        breaking = deep and two_substantial and not onset
        result["gaps"].append(
            {
                "span": gap["span"],
                "duration_ms": gap["duration_ms"],
                "depression_db": depth,
                "deep": deep,
                "two_substantial": two_substantial,
                "edge_fricative_onset": onset,
                "ownership_breaking": breaking,
            }
        )
        if candidate == "GAP_AWARE_AZURE" and breaking:
            return reject("deep_split_between_substantial_islands", "ambiguous")
    result.update(ownership="safe", representation="usable", reason="acoustically_supported_azure")
    return result

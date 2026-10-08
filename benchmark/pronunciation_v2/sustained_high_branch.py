"""Run-level acoustic diagnostics, deliberately NOT a production selector.

Measured candidates only. No text, inferred lower F0, interpolation, corpus
identity, or frequency-based human-range assumptions enter these features.
"""

from __future__ import annotations

import math
import statistics
from itertools import pairwise
from typing import Any

import numpy as np

from benchmark.pronunciation_v2.octave_ambiguity import branches, context_model, semitones


def nearest_candidate(frame: dict, ratio: float, tolerance_st: float = 1.0) -> dict | None:
    hz = frame.get("raw_f0_hz") or frame.get("selected_f0_hz")
    if hz is None:
        return None
    candidates = [
        dict(c, octave_error_st=abs(semitones(c["frequency_hz"] / (hz * ratio))))
        for c in frame["candidates"]
        if c["frequency_hz"] > 0 and c["frequency_hz"] != hz
    ]
    candidates = [c for c in candidates if c["octave_error_st"] <= tolerance_st]
    return min(candidates, key=lambda c: c["octave_error_st"], default=None)


def describe_path(frames: list[dict], indices: list[int], ratio: float) -> dict:
    """Coverage uses ALL run frames, including pre-existing selection gaps.

    Fixed +/-1 st octave tolerance and .45 candidate strength match the prior
    research definition. Report weak/missing frames; never fill them. Consecutive
    step statistics use consecutive SOURCE indices, not a bridge over a gap.
    """
    measured = [(i, nearest_candidate(frames[i], ratio)) for i in indices]
    present = [(i, c) for i, c in measured if c is not None]
    credible = [(i, c) for i, c in present if c["strength"] >= 0.45]
    deficits = [frames[i]["periodicity"] - c["strength"] for i, c in present]
    steps = [
        semitones(b["frequency_hz"] / a["frequency_hz"])
        for (i, a), (j, b) in pairwise(present)
        if j == i + 1
    ]
    curvature = [
        semitones(c["frequency_hz"] / b["frequency_hz"])
        - semitones(b["frequency_hz"] / a["frequency_hz"])
        for (i, a), (j, b), (k, c) in zip(present, present[1:], present[2:], strict=False)
        if j == i + 1 and k == j + 1
    ]
    streak = longest = 0
    for _, c in measured:
        streak = streak + 1 if c is not None and c["strength"] >= 0.45 else 0
        longest = max(longest, streak)
    return dict(
        ratio=ratio,
        run_frames=len(indices),
        present_frames=len(present),
        coverage=len(present) / len(indices),
        credible_frames=len(credible),
        credible_coverage=len(credible) / len(indices),
        bounded_deficit_frames=sum(
            frames[i]["periodicity"] - c["strength"] <= 0.25 for i, c in credible
        ),
        missing_indices=[i for i, c in measured if c is None],
        weak_indices=[i for i, c in present if c["strength"] < 0.45],
        median_strength_deficit=statistics.median(deficits) if deficits else None,
        maximum_strength_deficit=max(deficits, default=None),
        median_abs_step_st=statistics.median(map(abs, steps)) if steps else None,
        maximum_abs_step_st=max(map(abs, steps), default=None),
        rms_step_st=math.sqrt(statistics.fmean(s * s for s in steps)) if steps else None,
        rms_curvature_st=math.sqrt(statistics.fmean(s * s for s in curvature))
        if curvature
        else None,
        longest_credible_contiguous_frames=longest,
        path=[
            dict(index=i, timestamp_seconds=frames[i]["timestamp_seconds"], **c) for i, c in present
        ],
    )


def run_features(frames: list[dict], indices: list[int]) -> dict:
    """Two-sided context is an explicit requirement of the tentative screen.

    Use only the immediate neighboring selected branch's five contiguous edge
    samples. Compare boundary candidates to <=120 ms extrapolations at that
    boundary; never extrapolate a slope through an entire sustained run.
    """
    paths = [describe_path(frames, indices, ratio) for ratio in (0.25, 0.5, 2, 4)]
    all_runs = branches(frames)
    left = [r for r in all_runs if r[-1] < indices[0]]
    right = [r for r in all_runs if r[0] > indices[-1]]
    contexts: dict[str, Any] = {}
    for side, neighbor, before in (
        ("before", left[-1] if left else [], True),
        ("after", right[0] if right else [], False),
    ):
        model = context_model(frames, neighbor, before=before) if neighbor else None
        index = indices[0] if before else indices[-1]
        t = frames[index]["timestamp_seconds"]
        if model and abs(t - model["edge"]) <= 0.12 + 1e-9:
            prediction = model["intercept"] + model["slope"] * (t - model["center"])
            contexts[side] = dict(**model, prediction_hz=2 ** (prediction / 12))
        else:
            contexts[side] = None
    for path in paths:
        connections = {}
        for side, edge in (("before", indices[0]), ("after", indices[-1])):
            context = contexts[side]
            candidate = nearest_candidate(frames[edge], path["ratio"])
            if context is None or candidate is None:
                connections[side] = None
                continue
            hz = frames[edge].get("raw_f0_hz") or frames[edge]["selected_f0_hz"]
            high_residual = abs(semitones(hz / context["prediction_hz"]))
            alt_residual = abs(semitones(candidate["frequency_hz"] / context["prediction_hz"]))
            connections[side] = dict(
                selected_residual_st=high_residual,
                alternate_residual_st=alt_residual,
                advantage_st=high_residual - alt_residual,
            )
        path["connections"] = connections
    duration = (
        frames[indices[-1]]["timestamp_seconds"] - frames[indices[0]]["timestamp_seconds"] + 0.01
    )
    return dict(
        indices=indices,
        start=frames[indices[0]]["timestamp_seconds"],
        end=frames[indices[-1]]["timestamp_seconds"],
        sample_span_seconds=duration - 0.01,
        hop_support_seconds=duration,
        selected_frames=sum(frames[i]["selected_f0_hz"] is not None for i in indices),
        contexts=contexts,
        paths=paths,
    )


def screening_failures(features: dict, path: dict) -> list[str]:
    """One illustrative fixed screen, NOT an accepted ambiguity label.

    Even passing cannot establish acoustic ambiguity: genuine periodic signals
    have candidates at multiples of their shortest period. Independent acoustic
    evidence and genuine register-transition safety are still required.
    No parameter search is justified if the target fails these prerequisites.
    """
    failures = []
    if features["hop_support_seconds"] < 0.12 - 1e-9:
        failures.append("duration_below_120ms")
    if path["bounded_deficit_frames"] / path["run_frames"] < 0.8:
        failures.append("credible_bounded_coverage_below_80pct")
    if path["maximum_abs_step_st"] is None or path["maximum_abs_step_st"] > 3:
        failures.append("alternate_not_locally_continuous")
    for side in ("before", "after"):
        connection = path["connections"][side]
        if connection is None:
            failures.append(f"no_{side}_connection")
        elif connection["advantage_st"] < 6 or connection["alternate_residual_st"] > 3:
            failures.append(f"unsupported_{side}_connection")
    return failures


def spectral_slice(rate: int, values: np.ndarray, timestamp: float, seconds: float = 0.06) -> tuple:
    n = round(rate * seconds)
    center = round(timestamp * rate)
    data = values[max(0, center - n // 2) : center + n // 2].copy()
    data -= data.mean()
    nfft = 1 << (max(len(data), rate * 2) - 1).bit_length()
    power = abs(np.fft.rfft(data * np.hanning(len(data)), nfft)) ** 2
    frequency = np.fft.rfftfreq(nfft, 1 / rate)
    return frequency, power


def spectral_evidence(rate: int, values: np.ndarray, t: float, hz: float) -> dict:
    """60 and 100 ms Hann slices: zero padding interpolates, not resolves.

    Return every resolved local maximum <=2 kHz above -45 dB and maxima in
    hypothesis bands. Bands contain energy, not necessarily resolved peaks.
    A weak/absent fundamental alone never falsifies a harmonic series.
    """
    output = {}
    for width in (0.06, 0.1):
        f, p = spectral_slice(rate, values, t, width)
        mask = (f >= 40) & (f <= 2000)
        maximum = max(float(p[mask].max()), 1e-30)
        peaks = np.flatnonzero((p[1:-1] > p[:-2]) & (p[1:-1] > p[2:])) + 1
        peaks = [i for i in peaks if mask[i] and p[i] / maximum >= 10**-4.5]

        def band(target: float, frequencies=f, power=p, reference=maximum) -> dict:
            ix = np.flatnonzero(abs(frequencies - target) <= 12)
            i = ix[np.argmax(power[ix])]
            return dict(
                target_hz=target,
                peak_hz=float(frequencies[i]),
                db=float(10 * np.log10(max(power[i], 1e-30) / reference)),
            )

        output[str(width)] = dict(
            window_seconds=width,
            native_bin_hz=1 / width,
            peaks_hz_db=[[float(f[i]), float(10 * np.log10(p[i] / maximum))] for i in peaks],
            hypothesis_bands={
                name: [band(hz * ratio * k) for k in range(1, count + 1)]
                for name, ratio, count in (("high", 1, 4), ("half", 0.5, 8), ("quarter", 0.25, 12))
            },
        )
    return output


def period_evidence(
    rate: int, values: np.ndarray, t: float, hz: float, seconds: float = 0.06
) -> dict:
    """Waveform self-similarity; no path tracking or F0 output.

    Overlap-normalized, DC-centered lag comparison of the unfiltered signal.
    Search 1.5--23 ms and retain ALL local maxima, not just the best one.
    """
    center, half = round(t * rate), round(seconds * rate / 2)
    x = values[max(0, center - half) : center + half].copy()
    x -= x.mean()
    lags = np.arange(round(0.0015 * rate), min(round(0.023 * rate), len(x) // 2))
    correlations = np.array(
        [
            np.dot(x[:-lag], x[lag:])
            / max(1e-30, np.linalg.norm(x[:-lag]) * np.linalg.norm(x[lag:]))
            for lag in lags
        ]
    )
    peaks = (
        np.flatnonzero(
            (correlations[1:-1] > correlations[:-2]) & (correlations[1:-1] > correlations[2:])
        )
        + 1
    )

    def hypothesis(ratio: float) -> dict | None:
        period = 1 / (hz * ratio)
        ix = np.flatnonzero(abs(lags / rate - period) <= period * 0.08)
        if not len(ix):
            return None
        i = ix[np.argmax(correlations[ix])]
        return dict(period_ms=float(lags[i] / rate * 1000), correlation=float(correlations[i]))

    return dict(
        window_seconds=seconds,
        hypotheses={
            name: hypothesis(ratio)
            for name, ratio in (("high", 1), ("half", 0.5), ("quarter", 0.25), ("double", 2))
        },
        peaks=[
            dict(period_ms=float(lags[i] / rate * 1000), correlation=float(correlations[i]))
            for i in peaks
        ],
        lag_ms=(lags / rate * 1000).tolist(),
        correlation=correlations.tolist(),
    )

"""Bounded, offline octave-candidate experiment. NOT a production selector.

Replay only the six private physical captures and saved production controls. No
other estimator, VAD, linguistic input, frequency repair, or network access.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import asdict, dataclass
from itertools import pairwise
from typing import Any


@dataclass(frozen=True)
class Parameters:
    octave_tolerance_st: float = 1.0
    strength_margin: float = 0.25
    trajectory_advantage_st: float = 6.0
    maximum_run_seconds: float = 0.12


DEFAULT_PARAMETERS = Parameters()


def semitones(hz: float) -> float:
    return 12 * math.log2(hz)


def branches(frames: list[dict[str, Any]]) -> list[list[int]]:
    """Selected branch runs; permit <=45 ms between surviving measurements.

    This is diagnostic grouping, never interpolation or a display connection.
    A >6 st transition starts a new branch. A smooth broad sweep stays one run.
    """
    runs: list[list[int]] = []
    for i, frame in enumerate(frames):
        if frame["selected_f0_hz"] is None:
            continue
        last = frames[runs[-1][-1]] if runs else None
        if (
            last is None
            or frame["timestamp_seconds"] - last["timestamp_seconds"] > 0.045 + 1e-9
            or abs(semitones(frame["selected_f0_hz"] / last["selected_f0_hz"])) > 6
        ):
            runs.append([])
        runs[-1].append(i)
    return runs


def context_model(
    frames: list[dict[str, Any]], indices: list[int], *, before: bool
) -> dict[str, Any] | None:
    """Five nearest measured points, median slope and robust intercept.

    Context must itself be contiguous and locally coherent (<=2 st spread).
    Prediction is bounded to 120 ms by the caller. No frequency is synthesized
    for output; this is only a residual comparison between measured candidates.
    """
    indices = indices[-5:] if before else indices[:5]
    if len(indices) < 5 or any(b != a + 1 for a, b in pairwise(indices)):
        return None
    times = [frames[i]["timestamp_seconds"] for i in indices]
    values = [semitones(frames[i]["selected_f0_hz"]) for i in indices]
    if max(values) - min(values) > 2 or max(b - a for a, b in pairwise(times)) > 0.045:
        return None
    slope = statistics.median(
        (b - a) / (tb - ta)
        for a, b, ta, tb in zip(values, values[1:], times, times[1:], strict=False)
    )
    center = statistics.median(times)
    intercept = statistics.median(
        v - slope * (t - center) for v, t in zip(values, times, strict=True)
    )
    return dict(
        indices=indices,
        center=center,
        intercept=intercept,
        slope=slope,
        edge=times[-1] if before else times[0],
    )


def experiment(
    frames: list[dict[str, Any]],
    params: Parameters = DEFAULT_PARAMETERS,
    *,
    require_complete_run: bool = False,
) -> dict[str, Any]:
    """Reject only measured octave alternatives with strong local advantage.

    A frame's candidate must reach the existing 0.45 periodicity floor and be
    within the selected strength margin. Consider exact octave powers 1/4,
    1/2, 2 and 4 within the ratio tolerance. Require <=3 st candidate prediction
    residual and >=the configured improvement over selected pitch on *every*
    available stable side. One side is permitted, never a distant context.

    Candidate-poor frames are not swept into a rejected run. Long branches
    cannot be chopped into short eligible pieces to evade the duration bound.
    """
    runs = branches(frames)
    rejected: list[int] = []
    evidence: list[dict[str, Any]] = []
    for n, run in enumerate(runs):
        duration = frames[run[-1]]["timestamp_seconds"] - frames[run[0]]["timestamp_seconds"] + 0.01
        if duration > params.maximum_run_seconds + 1e-9:
            continue
        contexts = []
        for neighbor, before in ((n - 1, True), (n + 1, False)):
            if not 0 <= neighbor < len(runs):
                continue
            context = context_model(frames, runs[neighbor], before=before)
            edge = frames[run[0] if before else run[-1]]["timestamp_seconds"]
            if context and abs(edge - context["edge"]) <= 0.12 + 1e-9:
                contexts.append(context)
        if not contexts:
            continue
        for i in run:
            frame = frames[i]
            t, hz = frame["timestamp_seconds"], frame["selected_f0_hz"]
            predictions = [c["intercept"] + c["slope"] * (t - c["center"]) for c in contexts]
            # Bound each one-sided extrapolation, including the far run edge.
            if any(abs(t - c["edge"]) > 0.12 + 1e-9 for c in contexts):
                continue
            alternatives = []
            for candidate in frame["candidates"]:
                delta = semitones(candidate["frequency_hz"] / hz)
                octave = min((-24, -12, 12, 24), key=lambda k: abs(delta - k))
                margin = frame["periodicity"] - candidate["strength"]
                if (
                    abs(delta - octave) > params.octave_tolerance_st
                    or candidate["strength"] < 0.45
                    or margin > params.strength_margin
                ):
                    continue
                residuals = [abs(semitones(candidate["frequency_hz"]) - p) for p in predictions]
                advantages = [
                    abs(semitones(hz) - p) - r for p, r in zip(predictions, residuals, strict=True)
                ]
                if max(residuals) <= 3 and min(advantages) >= params.trajectory_advantage_st:
                    alternatives.append(
                        dict(
                            **candidate,
                            strength_margin=margin,
                            ratio=candidate["frequency_hz"] / hz,
                            nearest_octave_ratio=2 ** (octave / 12),
                            ratio_error_st=abs(delta - octave),
                            residual_st=max(residuals),
                            advantage_st=min(advantages),
                        )
                    )
            if alternatives:
                alternate = min(alternatives, key=lambda c: c["residual_st"])
                rejected.append(i)
                evidence.append(
                    dict(
                        index=i,
                        timestamp_seconds=t,
                        selected_f0_hz=hz,
                        alternate=alternate,
                        branch_indices=run,
                        branch_duration_seconds=duration,
                        contexts=contexts,
                        reason="octave_candidate_ambiguous",
                    )
                )
    if require_complete_run:
        eligible = set(rejected)
        evidence = [e for e in evidence if set(e["branch_indices"]) <= eligible]
        rejected = [e["index"] for e in evidence]
    rejected_runs: list[list[int]] = []
    for i in rejected:
        if not rejected_runs or i != rejected_runs[-1][-1] + 1:
            rejected_runs.append([])
        rejected_runs[-1].append(i)
    return dict(
        parameters=asdict(params),
        require_complete_run=require_complete_run,
        rejected_indices=rejected,
        runs=rejected_runs,
        evidence=evidence,
    )


def parameter_neighborhood() -> dict[str, Parameters]:
    """One factor at a time, not a fitted search."""
    return {
        "central": Parameters(),
        "ratio_0.75": Parameters(octave_tolerance_st=0.75),
        "ratio_1.25": Parameters(octave_tolerance_st=1.25),
        "margin_0.20": Parameters(strength_margin=0.20),
        "margin_0.30": Parameters(strength_margin=0.30),
        "advantage_5": Parameters(trajectory_advantage_st=5),
        "advantage_7": Parameters(trajectory_advantage_st=7),
        "duration_0.10": Parameters(maximum_run_seconds=0.10),
        "duration_0.14": Parameters(maximum_run_seconds=0.14),
    }

"""Dev product adapter: numeric acoustic selection, then separate expectation comparison."""

from __future__ import annotations

import math
import time
from itertools import pairwise
from pathlib import Path
from typing import Any

from pypinyin.contrib.tone_convert import to_tone, to_tone3

from benma_api.pronunciation.learned_contracts import (
    LearnedAnalysis,
    LearnedComparison,
    LearnedRealization,
    LearnedUnit,
)
from benma_api.pronunciation.learned_runtime import infer_batch
from benma_api.pronunciation.surface import SurfaceExpectation
from benma_api.schemas import PerceivedSyllable, SentencePitchEvidence


def refine_span(
    whole: list[float] | None,
    retained: list[float],
    raw: dict[str, Any],
    duration: float,
) -> LearnedRealization:
    """Frozen 10 ms cell envelope and >15 ms + below-existing-gate guard.

    No Hanzi, pitch value, tone, model prediction, or speaker input is accepted.
    Missing acoustic metadata fails closed, including unvoiced frame energy.
    """
    result = LearnedRealization()
    if (
        whole is None
        or len(whole) != 2
        or not all(type(t) in (int, float) and math.isfinite(t) for t in whole)
        or not 0 <= whole[0] < whole[1] <= duration
    ):
        result.reason = "invalid_or_missing_azure_timing"
        return result
    result.azure_span = whole
    result.context_span = [max(0, whole[0] - 0.25), min(duration, whole[1] + 0.25)]
    threshold = raw.get("energy_gate", {}).get("threshold_rms")
    frames = raw.get("f0", [])
    if (
        not isinstance(threshold, (int, float))
        or not math.isfinite(threshold)
        or threshold <= 0
        or not frames
        or any(
            not isinstance(p.get(k), (int, float)) or not math.isfinite(p[k])
            for p in frames
            for k in ("timestamp_seconds", "energy_rms")
        )
    ):
        result.reason = "missing_acoustic_validity_metadata"
        return result
    points = sorted(t for t in retained if whole[0] <= t < whole[1])
    result.retained_frames = len(points)
    if not points:
        result.reason = "no_voiced_support_in_tone_bearing_span"
        return result
    result.pooling_span = [max(whole[0], points[0] - 0.005), min(whole[1], points[-1] + 0.005)]
    interruptions = []
    for left, right in pairwise(points):
        if right - left <= 0.015:
            continue
        between = [p for p in frames if left < p["timestamp_seconds"] < right]
        if not between:
            result.reason = "missing_intervening_acoustic_frames"
            return result
        low = [p["timestamp_seconds"] for p in between if p["energy_rms"] < threshold]
        if low:
            interruptions.append(
                {
                    "between_retained_centers": [left, right],
                    "below_existing_energy_gate_centers": low,
                }
            )
    result.continuity = {
        "checked": True,
        "passed": not interruptions,
        "threshold_rms": threshold,
        "interruptions": interruptions,
        "maximum_adjacent_gap_seconds": 0.015,
    }
    if interruptions:
        result.reason = "ambiguous_interrupted_voiced_envelope"
    elif result.pooling_span[1] - result.pooling_span[0] < 0.06 - 1e-9:
        result.reason = "too_little_material"
    return result


def comparison(
    expected: int | SurfaceExpectation | None, realization: LearnedRealization
) -> LearnedComparison:
    surface = (
        expected
        if isinstance(expected, SurfaceExpectation)
        else SurfaceExpectation(expected, "saved")
    )
    if surface.tone == 0:
        return LearnedComparison(
            state="neutral", message="Neutral syllable: no numbered-tone correction."
        )
    if realization.status != "ok" or realization.prediction is None:
        return LearnedComparison(state="insufficient", message="Not enough evidence")
    heard = f"Tone {realization.prediction[-1]}"
    if not surface.acceptable_tones:
        return LearnedComparison(
            state="unresolved",
            message=(f"Heard {heard}. Benma can't reliably grade this tone in context yet."),
        )
    match = int(realization.prediction[-1]) in surface.acceptable_tones
    target = " or ".join(f"Tone {tone}" for tone in surface.acceptable_tones)
    here = " here" if surface.contextual_rule else ""
    return LearnedComparison(
        state="experimental_match" if match else "experimental_mismatch",
        message=f"Correct · {heard}{here}" if match else f"Expected {target}{here} · heard {heard}",
    )


def supported_explanation(syllable: PerceivedSyllable, result: LearnedRealization) -> str | None:
    # Direct measurement only. No assertion of an absent recovery or a lexical error.
    if syllable.pitch_eligibility.state != "sufficient" or result.status != "ok":
        return None
    contour = syllable.observed_contour
    if (
        contour.confidence != "moderate"
        or contour.classification != f"{(result.prediction or '')[-1:]}-like"
    ):
        return None
    change = contour.features.get("change_st")
    if change is None or not math.isfinite(change):
        return None
    if result.prediction == "T4" and change < 0:
        return f"Measured pitch fell by {abs(change):.2f} semitones."
    if result.prediction == "T2" and change > 0:
        return f"Measured pitch rose by {change:.2f} semitones."
    return None


def analyze_learned(
    *,
    audio: Path,
    sha256: str,
    duration: float,
    syllables: list[PerceivedSyllable],
    graph: SentencePitchEvidence,
    raw: dict[str, Any],
    recorded: bool,
    expected: list[PerceivedSyllable],
    target_text: str,
    intended: bool,
    surfaces: list[SurfaceExpectation] | None = None,
) -> LearnedAnalysis:
    started = time.perf_counter()
    retained = [p.timestamp_seconds for segment in graph.filtered.segments for p in segment]
    realizations, contracts, positions = [], [], []
    for s in syllables:
        # Only the application's exact Azure-owned character spans are eligible.
        whole = (
            [s.start_seconds, s.end_seconds]
            if (
                recorded
                and s.start_seconds is not None
                and s.end_seconds is not None
                and s.timing_source in {"azure_provider_grapheme", "azure_character_word"}
            )
            else None
        )
        realization = refine_span(whole, retained, raw, duration)
        # Scope is downstream of generic selection; no numbered expectation reaches infer.
        if expected[s.index].expected_surface_tone == 0:
            realization.reason = realization.reason or "neutral_outside_four_tone_model"
        if not realization.reason:
            contracts.append(
                {
                    "audio_reference": str(audio),
                    "audio_sha256": sha256,
                    "read_unit": realization.azure_span,
                    "pooling": realization.pooling_span,
                    "context": realization.context_span,
                }
            )
            positions.append(s.index)
        realizations.append(realization)
    refinement_ms = (time.perf_counter() - started) * 1000
    outputs, runtime = infer_batch(contracts)
    for index, output in zip(positions, outputs, strict=True):
        # Explicit output allowlist: absolute paths/caches never enter public responses.
        for key in (
            "status",
            "reason",
            "prediction",
            "confidence",
            "probabilities",
            "owned_encoder_frames",
        ):
            if key in output:
                setattr(realizations[index], key, output[key])
    grading = time.perf_counter()
    units = []
    surfaces = (
        surfaces
        if surfaces is not None
        else [
            SurfaceExpectation(e.expected_surface_tone, e.surface_rule or "saved") for e in expected
        ]
    )
    for s, e, realized, surface in zip(syllables, expected, realizations, surfaces, strict=True):
        grade = comparison(surface, realized)
        if grade.state == "experimental_mismatch":
            grade.explanation = supported_explanation(s, realized)
        numeric = to_tone3(e.pinyin, neutral_tone_with_five=True) if e.pinyin else None
        heard = (
            to_tone(numeric[:-1] + realized.prediction[-1])
            if (numeric and realized.prediction and numeric[-1:] in "12345")
            else None
        )
        units.append(
            LearnedUnit(
                index=s.index,
                characters=e.characters,
                target_pinyin=e.pinyin,
                lexical_tone=e.lexical_tone,
                expected_surface_tone=surface.tone,
                acceptable_surface_tones=list(surface.acceptable_tones),
                expected_neutral=surface.tone == 0,
                expectation_resolution=surface.resolution,
                surface_rule=surface.rule,
                contextual_rule=surface.contextual_rule,
                heard_pinyin=heard,
                realization=realized,
                comparison=grade,
            )
        )
    return LearnedAnalysis(
        expectation_basis="intended_target" if intended else "perceived_text",
        target_text=target_text,
        units=units,
        runtime=runtime,
        timings_ms={
            "local_refinement": refinement_ms,
            "grading": (time.perf_counter() - grading) * 1000,
            **{k: v for k, v in runtime.items() if k.endswith("_ms")},
        },
    )

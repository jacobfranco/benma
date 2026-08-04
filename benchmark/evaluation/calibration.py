"""Human-supported pronunciation calibration math and immutable split policy."""

from __future__ import annotations

import hashlib
import math
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from itertools import pairwise
from pathlib import Path
from typing import Any

from benchmark.models import (
    BenchmarkSample,
    CalibrationMode,
    CalibrationScope,
    CalibrationSplitManifest,
    ErrorType,
    HumanConsensusClass,
    HumanListenerAnnotation,
    RecordingQualityEvidence,
    SemanticSeverity,
    SpeakerCategory,
)
from benchmark.storage import load_model, write_model


@dataclass(frozen=True, slots=True)
class RateEstimate:
    numerator: int
    denominator: int
    fraction: float | None
    confidence_interval_95: tuple[float, float] | None

    def normalized(self) -> dict[str, Any]:
        return asdict(self)


def rate_estimate(numerator: int, denominator: int) -> RateEstimate:
    if denominator <= 0:
        return RateEstimate(numerator=0, denominator=0, fraction=None, confidence_interval_95=None)
    fraction = numerator / denominator
    z = 1.959963984540054
    denominator_adjustment = 1 + z * z / denominator
    center = (fraction + z * z / (2 * denominator)) / denominator_adjustment
    margin = (
        z
        * math.sqrt(
            fraction * (1 - fraction) / denominator + z * z / (4 * denominator**2)
        )
        / denominator_adjustment
    )
    return RateEstimate(
        numerator=numerator,
        denominator=denominator,
        fraction=fraction,
        confidence_interval_95=(max(0.0, center - margin), min(1.0, center + margin)),
    )


def qualifying_native_annotations(
    annotations: Iterable[HumanListenerAnnotation],
) -> list[HumanListenerAnnotation]:
    return [
        annotation
        for annotation in annotations
        if annotation.blind.rater_profile is not None
        and annotation.blind.rater_profile.native_mandarin_self_report
    ]


def _vote(items: Sequence[bool]) -> dict[str, int | bool | None]:
    yes = sum(items)
    total = len(items)
    return {
        "yes": yes,
        "no": total - yes,
        "total": total,
        "majority": yes >= 2 if total >= 3 else None,
        "unanimous": yes == total if total else None,
    }


def _tone(value: str | None) -> str | None:
    if value is None:
        return None
    upper = value.upper()
    if upper in {"UNKNOWN", "INVALID"}:
        return upper
    digits = [character for character in upper if character in "012345"]
    if not digits:
        return None
    return "T0" if digits[-1] == "5" else f"T{digits[-1]}"


def consensus_for_sample(
    sample: BenchmarkSample, annotations: Sequence[HumanListenerAnnotation]
) -> dict[str, Any]:
    native = qualifying_native_annotations(annotations)
    revealed = [item.revealed for item in native if item.revealed is not None]
    understood = _vote([item.blind.response.understood_first_pass for item in native])
    repeat = _vote([item.blind.response.would_request_repetition for item in native])
    tone_issue = _vote([item.response.tone_problem for item in revealed])
    initial_issue = _vote([item.response.initial_problem for item in revealed])
    final_issue = _vote([item.response.final_problem for item in revealed])
    invalid = _vote([item.response.invalid_sample for item in revealed])
    technical_majority = any(
        vote["majority"] is True for vote in (tone_issue, initial_issue, final_issue)
    )
    quality_invalid = (
        isinstance(sample.recording_quality, RecordingQualityEvidence)
        and sample.recording_quality.status == "invalid"
    )
    if invalid["majority"] is True or quality_invalid:
        consensus_class = HumanConsensusClass.INVALID_SAMPLE
    elif len(native) < 3 or len(revealed) < 3:
        consensus_class = HumanConsensusClass.AMBIGUOUS
    elif repeat["majority"] is True or understood["majority"] is False:
        consensus_class = HumanConsensusClass.LIKELY_UNINTELLIGIBLE
    elif understood["unanimous"] is True and not technical_majority:
        consensus_class = HumanConsensusClass.STRONG_ACCEPT
    elif understood["majority"] is True and technical_majority:
        consensus_class = HumanConsensusClass.ACCEPTABLE_WITH_ERROR
    else:
        consensus_class = HumanConsensusClass.AMBIGUOUS

    severity_votes = [
        item.response.semantic_severity.value
        for item in revealed
        if item.response.semantic_severity is not None
    ]
    severity_counts = Counter(severity_votes)
    severity = severity_counts.most_common(1)[0][0] if severity_counts else None

    produced_tones: dict[int, str] = {}
    affected_tone_indices: Counter[int] = Counter()
    for item in revealed:
        if item.response.tone_problem:
            affected_tone_indices.update(item.response.affected_syllable_indices)
    for index in range(len(sample.intended_pinyin)):
        values = [
            _tone(item.response.perceived_produced_tones[index])
            for item in revealed
            if index < len(item.response.perceived_produced_tones)
        ]
        counts = Counter(value for value in values if value is not None)
        if counts:
            value, count = counts.most_common(1)[0]
            if count >= 2:
                produced_tones[index] = value

    return {
        "qualifying_native_listener_count": len(native),
        "stage_b_count": len(revealed),
        "understood_first_pass": understood,
        "would_request_repetition": repeat,
        "tone_issue": tone_issue,
        "initial_issue": initial_issue,
        "final_issue": final_issue,
        "invalid_sample": invalid,
        "consensus_class": consensus_class.value,
        "semantic_severity": severity,
        "human_supported_tone_error_indices": sorted(
            index for index, count in affected_tone_indices.items() if count >= 2
        ),
        "human_supported_produced_tones": {
            str(index): tone for index, tone in produced_tones.items()
        },
        "individual_annotations": [item.model_dump(mode="json") for item in annotations],
    }


def calibration_mode(sample: BenchmarkSample) -> CalibrationMode | None:
    if sample.calibration_mode is not None:
        return sample.calibration_mode
    error = sample.deliberate_error.error_type if sample.deliberate_error else ErrorType.NONE
    if error == ErrorType.WRONG_TONE:
        return CalibrationMode.LEARNER_INTENTIONAL_TONE_ERROR
    if error == ErrorType.WRONG_INITIAL:
        return CalibrationMode.LEARNER_INTENTIONAL_INITIAL_ERROR
    if error == ErrorType.WRONG_FINAL:
        return CalibrationMode.LEARNER_INTENTIONAL_FINAL_ERROR
    if sample.speaker_category == SpeakerCategory.NATIVE_CONTROL:
        return CalibrationMode.NATIVE_CONTROL
    if {"negative_control", "nonsense", "low_confidence"} & sample.tags:
        return CalibrationMode.NEGATIVE_CONTROL
    if sample.speaker_category == SpeakerCategory.LEARNER and error == ErrorType.NONE:
        return CalibrationMode.LEARNER_CORRECT
    return None


def create_stratified_split(
    samples: Sequence[BenchmarkSample], *, benchmark_version: str, split_version: str
) -> CalibrationSplitManifest:
    strata: dict[str, list[BenchmarkSample]] = defaultdict(list)
    for sample in samples:
        mode = calibration_mode(sample)
        quality = sample.recording_quality.status if sample.recording_quality else "unknown"
        strata[f"{mode.value if mode else 'other'}:{quality}"].append(sample)
    calibration_ids: list[str] = []
    held_out_ids: list[str] = []
    for stratum in sorted(strata):
        ordered = sorted(
            strata[stratum],
            key=lambda sample: hashlib.sha256(
                f"{split_version}:{stratum}:{sample.sample_id}".encode()
            ).hexdigest(),
        )
        holdout_count = 0 if len(ordered) < 2 else max(1, round(len(ordered) * 0.25))
        held_out_ids.extend(sample.sample_id for sample in ordered[:holdout_count])
        calibration_ids.extend(sample.sample_id for sample in ordered[holdout_count:])
    return CalibrationSplitManifest(
        benchmark_version=benchmark_version,
        split_version=split_version,
        calibration_sample_ids=tuple(sorted(calibration_ids)),
        held_out_sample_ids=tuple(sorted(held_out_ids)),
    )


def persist_split(path: Path, split: CalibrationSplitManifest) -> CalibrationSplitManifest:
    if path.exists():
        existing = load_model(path, CalibrationSplitManifest)
        if existing.model_dump(exclude={"created_at"}) != split.model_dump(
            exclude={"created_at"}
        ):
            raise ValueError(
                "split manifest is immutable; increment split_version for a new partition"
            )
        return existing
    write_model(path, split)
    return split


@dataclass(frozen=True, slots=True)
class BinaryObservation:
    sample_id: str
    score: float
    human_error: bool


def threshold_metrics(
    observations: Sequence[BinaryObservation], threshold: float
) -> dict[str, Any]:
    errors = [item for item in observations if item.human_error]
    acceptable = [item for item in observations if not item.human_error]
    false_accept = sum(item.score >= threshold for item in errors)
    false_reject = sum(item.score < threshold for item in acceptable)
    true_positive = len(errors) - false_accept
    true_negative = len(acceptable) - false_reject
    precision_denominator = true_positive + false_reject
    recall = true_positive / len(errors) if errors else None
    specificity = true_negative / len(acceptable) if acceptable else None
    return {
        "threshold": threshold,
        "false_acceptance": rate_estimate(false_accept, len(errors)).normalized(),
        "false_rejection": rate_estimate(false_reject, len(acceptable)).normalized(),
        "sensitivity": recall,
        "specificity": specificity,
        "balanced_accuracy": (
            (recall + specificity) / 2 if recall is not None and specificity is not None else None
        ),
        "precision": (
            true_positive / precision_denominator if precision_denominator else None
        ),
        "recall": recall,
    }


def explore_thresholds(
    observations: Sequence[BinaryObservation],
    *,
    split: CalibrationSplitManifest | None,
) -> list[dict[str, Any]]:
    if split is None:
        calibration = list(observations)
        held_out: list[BinaryObservation] = []
    else:
        calibration_ids = set(split.calibration_sample_ids)
        held_out_ids = set(split.held_out_sample_ids)
        calibration = [item for item in observations if item.sample_id in calibration_ids]
        held_out = [item for item in observations if item.sample_id in held_out_ids]
    values = sorted({item.score for item in calibration})
    if not values:
        return []
    thresholds = sorted(
        {values[0], values[-1]}
        | {(left + right) / 2 for left, right in pairwise(values)}
    )
    return [
        {
            "selected": False,
            "promotion_state": "exploratory_only",
            "calibration": threshold_metrics(calibration, threshold),
            "held_out": threshold_metrics(held_out, threshold) if held_out else None,
        }
        for threshold in thresholds
    ]


def severity_is_severe(
    value: str | None, consensus_class: str | None = None
) -> bool:
    return consensus_class == HumanConsensusClass.LIKELY_UNINTELLIGIBLE.value or value in {
        SemanticSeverity.REQUIRES_REPETITION.value,
        SemanticSeverity.WRONG_WORD_PERCEIVED.value,
    }


def calibration_scope_for_promotion(
    *,
    held_out_gate_passed: bool,
    learner_speaker_ids: set[str],
    pilot_population_gate_passed: bool = False,
    representative_general_study_passed: bool = False,
) -> CalibrationScope:
    if not held_out_gate_passed:
        return CalibrationScope.NONE
    if representative_general_study_passed:
        return CalibrationScope.GENERAL
    if len(learner_speaker_ids) == 1:
        return CalibrationScope.PERSONAL
    if pilot_population_gate_passed and len(learner_speaker_ids) > 1:
        return CalibrationScope.PILOT_POPULATION
    return CalibrationScope.NONE

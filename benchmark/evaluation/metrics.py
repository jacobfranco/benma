"""Exact, auditable metric definitions used by report generation."""

from __future__ import annotations

import math
import re
import statistics
import unicodedata
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from benchmark.models import (
    BenchmarkSample,
    BlindAnnotationCommit,
    ErrorType,
    KnownTargetAssessmentResult,
    ProviderRun,
    RunStatus,
    SpeakerCategory,
    UnknownTargetPerceptionResult,
)


def normalize_transcript(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower()
    return "".join(
        character
        for character in normalized
        if not character.isspace() and not unicodedata.category(character).startswith("P")
    )


def edit_distance(reference: Sequence[object], hypothesis: Sequence[object]) -> int:
    previous = list(range(len(hypothesis) + 1))
    for ref_index, ref_item in enumerate(reference, start=1):
        current = [ref_index]
        for hyp_index, hyp_item in enumerate(hypothesis, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[hyp_index] + 1,
                    previous[hyp_index - 1] + (ref_item != hyp_item),
                )
            )
        previous = current
    return previous[-1]


def character_error_rate(reference: str, hypothesis: str) -> float | None:
    ref = normalize_transcript(reference)
    hyp = normalize_transcript(hypothesis)
    return edit_distance(ref, hyp) / len(ref) if ref else None


def word_error_rate(reference: str, hypothesis: str) -> float | None:
    ref = [token for token in re.split(r"\s+", reference.strip()) if token]
    hyp = [token for token in re.split(r"\s+", hypothesis.strip()) if token]
    if len(ref) <= 1:
        return None
    return edit_distance(ref, hyp) / len(ref)


def quantile(values: Sequence[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    low, high = math.floor(index), math.ceil(index)
    if low == high:
        return ordered[low]
    return ordered[low] * (high - index) + ordered[high] * (index - low)


def inter_rater_pairwise_cer(annotations: Sequence[BlindAnnotationCommit]) -> float | None:
    by_sample: dict[str, list[str]] = defaultdict(list)
    for annotation in annotations:
        by_sample[annotation.sample_id].append(annotation.response.perceived_text)
    distances: list[float] = []
    for texts in by_sample.values():
        for left_index, left in enumerate(texts):
            for right in texts[left_index + 1 :]:
                forward = character_error_rate(left, right)
                reverse = character_error_rate(right, left)
                if forward is not None and reverse is not None:
                    distances.append((forward + reverse) / 2)
    return statistics.fmean(distances) if distances else None


@dataclass(frozen=True)
class UnknownMetrics:
    attempted: int
    succeeded: int
    failed: int
    intended_cer: float | None
    intended_wer: float | None
    mean_human_cer: float | None
    error_preservation_recall: float | None
    semantic_repair_rate: float | None
    confidence_observations: int
    mean_confidence: float | None
    high_confidence_repair_rate: float | None
    context_leakage_delta: float | None
    p50_latency_seconds: float | None
    p95_latency_seconds: float | None
    estimated_cost_usd: float | None


def unknown_metrics(
    runs: Sequence[ProviderRun],
    samples: dict[str, BenchmarkSample],
    annotations: Sequence[BlindAnnotationCommit],
) -> UnknownMetrics:
    listeners: dict[str, list[BlindAnnotationCommit]] = defaultdict(list)
    for annotation in annotations:
        listeners[annotation.sample_id].append(annotation)
    succeeded = [
        run
        for run in runs
        if run.status == RunStatus.SUCCEEDED
        and isinstance(run.normalized_result, UnknownTargetPerceptionResult)
    ]
    intended_rates: list[float] = []
    word_rates: list[float] = []
    human_rates: list[float] = []
    eligible = 0
    preserved = 0
    repaired = 0
    confidences: list[float] = []
    eligible_with_confidence = 0
    high_confidence_repairs = 0
    no_context: dict[str, str] = {}
    contextual: dict[str, list[str]] = defaultdict(list)
    for run in succeeded:
        sample = samples.get(run.benchmark_sample_id)
        result = run.normalized_result
        assert isinstance(result, UnknownTargetPerceptionResult)
        if result.confidence is not None:
            confidences.append(result.confidence)
        if sample is None or not sample.intended_text:
            continue
        cer = character_error_rate(sample.intended_text, result.transcript)
        if cer is not None:
            intended_rates.append(cer)
        wer = word_error_rate(sample.intended_text, result.transcript)
        if wer is not None:
            word_rates.append(wer)
        sample_listeners = listeners.get(sample.sample_id, [])
        for annotation in sample_listeners:
            rate = character_error_rate(annotation.response.perceived_text, result.transcript)
            if rate is not None:
                human_rates.append(rate)
        error = sample.deliberate_error
        humans_heard_noncanonical = any(
            normalize_transcript(item.response.perceived_text)
            != normalize_transcript(sample.intended_text)
            for item in sample_listeners
        )
        if error is not None and error.error_type != ErrorType.NONE and humans_heard_noncanonical:
            eligible += 1
            if result.confidence is not None:
                eligible_with_confidence += 1
            if normalize_transcript(result.transcript) != normalize_transcript(
                sample.intended_text
            ):
                preserved += 1
            else:
                repaired += 1
                if result.confidence is not None and result.confidence >= 0.8:
                    high_confidence_repairs += 1
        if run.context_condition is not None:
            if run.context_condition.value.startswith("A_"):
                no_context[sample.sample_id] = result.transcript
            else:
                contextual[sample.sample_id].append(result.transcript)
    context_pairs = 0
    context_repairs = 0
    for sample_id, baseline in no_context.items():
        sample = samples.get(sample_id)
        if sample is None or not sample.intended_text:
            continue
        for transcript in contextual.get(sample_id, []):
            context_pairs += 1
            if normalize_transcript(baseline) != normalize_transcript(
                sample.intended_text
            ) and normalize_transcript(transcript) == normalize_transcript(sample.intended_text):
                context_repairs += 1
    latencies = [
        run.response_latency_seconds
        for run in succeeded
        if run.response_latency_seconds is not None
    ]
    costs = [run.estimated_cost_usd for run in succeeded if run.estimated_cost_usd is not None]
    return UnknownMetrics(
        attempted=len(runs),
        succeeded=len(succeeded),
        failed=len(runs) - len(succeeded),
        intended_cer=statistics.fmean(intended_rates) if intended_rates else None,
        intended_wer=statistics.fmean(word_rates) if word_rates else None,
        mean_human_cer=statistics.fmean(human_rates) if human_rates else None,
        error_preservation_recall=preserved / eligible if eligible else None,
        semantic_repair_rate=repaired / eligible if eligible else None,
        confidence_observations=len(confidences),
        mean_confidence=statistics.fmean(confidences) if confidences else None,
        high_confidence_repair_rate=(
            high_confidence_repairs / eligible_with_confidence if eligible_with_confidence else None
        ),
        context_leakage_delta=context_repairs / context_pairs if context_pairs else None,
        p50_latency_seconds=quantile(latencies, 0.5),
        p95_latency_seconds=quantile(latencies, 0.95),
        estimated_cost_usd=sum(costs) if costs else None,
    )


@dataclass(frozen=True)
class KnownMetrics:
    attempted: int
    succeeded: int
    tone_observations: int
    tone_false_accept_rate: float | None
    native_false_reject_rate: float | None
    phone_error_recall: float | None
    initial_error_recall: float | None
    final_error_recall: float | None
    confusion: dict[str, dict[str, int]]
    unsupported_capabilities: tuple[str, ...]
    p50_latency_seconds: float | None
    p95_latency_seconds: float | None
    estimated_cost_usd: float | None


def known_metrics(
    runs: Sequence[ProviderRun],
    samples: dict[str, BenchmarkSample],
    *,
    accept_threshold: float | None = None,
) -> KnownMetrics:
    succeeded = [
        run
        for run in runs
        if run.status == RunStatus.SUCCEEDED
        and isinstance(run.normalized_result, KnownTargetAssessmentResult)
    ]
    confusion: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    wrong_tone_scored = 0
    wrong_tone_accepted = 0
    native = 0
    native_rejected = 0
    phone_errors = 0
    phone_errors_detected = 0
    initial_errors = 0
    initial_errors_detected = 0
    final_errors = 0
    final_errors_detected = 0
    observations = 0
    unsupported: set[str] = set()
    for run in succeeded:
        sample = samples.get(run.benchmark_sample_id)
        if sample is None:
            continue
        result = run.normalized_result
        assert isinstance(result, KnownTargetAssessmentResult)
        unsupported.update(result.unsupported_capabilities)
        for syllable in result.syllables:
            if syllable.reference_tone and syllable.detected_tone:
                confusion[syllable.reference_tone][syllable.detected_tone] += 1
                observations += 1
        error = sample.deliberate_error
        if error is not None and error.error_type == ErrorType.WRONG_TONE:
            index = error.corrupted_syllable_index
            target = (
                result.syllables[index]
                if index is not None and index < len(result.syllables)
                else None
            )
            if (
                accept_threshold is not None
                and target is not None
                and target.tone_score is not None
            ):
                wrong_tone_scored += 1
                accepted = target.tone_score >= accept_threshold
            else:
                accepted = False
            if accepted:
                wrong_tone_accepted += 1
        if sample.speaker_category == SpeakerCategory.NATIVE_CONTROL:
            native += 1
            score = (
                result.pronunciation_score
                if result.pronunciation_score is not None
                else result.overall_score
            )
            if (
                accept_threshold is not None
                and score is not None
                and score < accept_threshold
            ):
                native_rejected += 1
        if error is not None and error.error_type in {
            ErrorType.WRONG_INITIAL,
            ErrorType.WRONG_FINAL,
        }:
            phone_errors += 1
            if error.error_type == ErrorType.WRONG_INITIAL:
                initial_errors += 1
            else:
                final_errors += 1
            index = error.corrupted_syllable_index
            target = (
                result.syllables[index]
                if index is not None and index < len(result.syllables)
                else None
            )
            if target is not None:
                caught_by_class = bool(target.error_classifications)
                caught_by_score = (
                    accept_threshold is not None
                    and any(
                        phone.score is not None and phone.score < accept_threshold
                        for phone in target.phones
                    )
                )
                if caught_by_class or caught_by_score:
                    phone_errors_detected += 1
                    if error.error_type == ErrorType.WRONG_INITIAL:
                        initial_errors_detected += 1
                    else:
                        final_errors_detected += 1
    latencies = [
        run.response_latency_seconds
        for run in succeeded
        if run.response_latency_seconds is not None
    ]
    costs = [run.estimated_cost_usd for run in succeeded if run.estimated_cost_usd is not None]
    return KnownMetrics(
        attempted=len(runs),
        succeeded=len(succeeded),
        tone_observations=observations,
        tone_false_accept_rate=(
            wrong_tone_accepted / wrong_tone_scored if wrong_tone_scored else None
        ),
        native_false_reject_rate=(
            native_rejected / native if native and accept_threshold is not None else None
        ),
        phone_error_recall=phone_errors_detected / phone_errors if phone_errors else None,
        initial_error_recall=(initial_errors_detected / initial_errors if initial_errors else None),
        final_error_recall=final_errors_detected / final_errors if final_errors else None,
        confusion={expected: dict(detected) for expected, detected in confusion.items()},
        unsupported_capabilities=tuple(sorted(unsupported)),
        p50_latency_seconds=quantile(latencies, 0.5),
        p95_latency_seconds=quantile(latencies, 0.95),
        estimated_cost_usd=sum(costs) if costs else None,
    )

"""Real-only, human-supported pronunciation calibration report and truth gates."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from benchmark.annotations import load_annotation
from benchmark.evaluation.calibration import (
    BinaryObservation,
    calibration_mode,
    consensus_for_sample,
    explore_thresholds,
    rate_estimate,
    severity_is_severe,
)
from benchmark.evaluation.metrics import quantile
from benchmark.models import (
    AcousticAnalysisResult,
    BenchmarkSample,
    CalibrationMaturity,
    CalibrationMode,
    CalibrationRunManifest,
    CalibrationScope,
    CalibrationSplitManifest,
    CorpusManifest,
    EvidenceOrigin,
    HumanListenerAnnotation,
    KnownTargetAssessmentResult,
    ProviderRun,
    RequestMode,
    RunStatus,
    SpeakerCategory,
)
from benchmark.providers.status import provider_status_scorecard
from benchmark.storage import load_model, write_json, write_model

SYNTHETIC_ORIGINS = {
    EvidenceOrigin.DOCUMENTATION_CONTRACT_EXAMPLE,
    EvidenceOrigin.CONSTRUCTED_FIXTURE,
    EvidenceOrigin.SYNTHETIC_REPLAY,
}


def _runs(path: Path) -> list[ProviderRun]:
    return [load_model(item, ProviderRun) for item in sorted(path.glob("*.json"))]


def _annotations(path: Path) -> list[HumanListenerAnnotation]:
    blind = path / "blind"
    if not blind.exists():
        return []
    return [
        load_annotation(item, path / "revealed" / item.name)
        for item in sorted(blind.glob("*.json"))
    ]


def _tone(value: str | int | None) -> str | None:
    if value is None:
        return None
    upper = str(value).upper()
    if upper in {"UNKNOWN", "INVALID"}:
        return upper
    digits = [item for item in upper if item in "012345"]
    if not digits:
        return None
    return "T0" if digits[-1] == "5" else f"T{digits[-1]}"


def _provider_identity(run: ProviderRun) -> str:
    configuration = json.dumps(
        run.request_configuration, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    digest = hashlib.sha256(configuration.encode()).hexdigest()[:10]
    return f"{run.provider}/{run.product}#config-{digest}"


def _latest_evidence_runs(runs: list[ProviderRun]) -> tuple[list[ProviderRun], list[str]]:
    latest: dict[tuple[str, str], ProviderRun] = {}
    superseded: list[str] = []
    for run in sorted(runs, key=lambda item: (item.timestamp, item.run_id)):
        key = (run.benchmark_sample_id, _provider_identity(run))
        previous = latest.get(key)
        if previous is not None:
            superseded.append(previous.run_id)
        latest[key] = run
    return list(latest.values()), superseded


def _expected_tone(sample: BenchmarkSample, index: int, reference: str | None) -> str | None:
    if index < len(sample.expected_surface_tones):
        expected = _tone(sample.expected_surface_tones[index])
        if expected is not None:
            return expected
    if index < len(sample.lexical_tones):
        return _tone(sample.lexical_tones[index])
    return _tone(reference)


def _real_run(run: ProviderRun) -> bool:
    if run.evidence_origin in SYNTHETIC_ORIGINS:
        return False
    raw = run.raw_response
    return not (
        isinstance(raw, dict)
        and (
            raw.get("synthetic")
            or raw.get("fixture")
            or raw.get("capture_type")
            in {"DOCUMENTATION_CONTRACT_EXAMPLE", "CONSTRUCTED_FIXTURE", "SYNTHETIC_REPLAY"}
        )
    )


def _human_consensus(
    samples: dict[str, BenchmarkSample], annotations: list[HumanListenerAnnotation]
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[HumanListenerAnnotation]] = defaultdict(list)
    for annotation in annotations:
        grouped[annotation.blind.sample_id].append(annotation)
    return {
        sample_id: consensus_for_sample(samples[sample_id], items)
        for sample_id, items in grouped.items()
        if sample_id in samples
    }


def _human_evidence_summary(
    consensus: dict[str, dict[str, Any]],
    annotations: list[HumanListenerAnnotation],
) -> dict[str, Any]:
    understood_yes = sum(item["understood_first_pass"]["yes"] for item in consensus.values())
    understood_total = sum(
        item["understood_first_pass"]["total"] for item in consensus.values()
    )
    repeat_yes = sum(item["would_request_repetition"]["yes"] for item in consensus.values())
    repeat_total = sum(
        item["would_request_repetition"]["total"] for item in consensus.values()
    )
    return {
        "consensus_classes": dict(
            Counter(item["consensus_class"] for item in consensus.values())
        ),
        "understood_first_pass": rate_estimate(
            understood_yes, understood_total
        ).normalized(),
        "would_request_repetition": rate_estimate(repeat_yes, repeat_total).normalized(),
        "understanding_vote_patterns": dict(
            Counter(
                f"{item['understood_first_pass']['yes']}/{item['understood_first_pass']['total']}"
                for item in consensus.values()
            )
        ),
        "samples_with_understanding_disagreement": sum(
            0 < item["understood_first_pass"]["yes"]
            < item["understood_first_pass"]["total"]
            for item in consensus.values()
        ),
        "rater_roles": dict(
            Counter(
                annotation.blind.rater_profile.role.value
                for annotation in annotations
                if annotation.blind.rater_profile is not None
            )
        ),
    }


def _sample_group(sample: BenchmarkSample, human: dict[str, Any] | None) -> str:
    mode = calibration_mode(sample)
    if mode == CalibrationMode.NATIVE_CONTROL:
        return "native_control"
    if mode == CalibrationMode.NEGATIVE_CONTROL:
        return "negative_control"
    if human and severity_is_severe(
        human.get("semantic_severity"), human.get("consensus_class")
    ):
        return "severe_error"
    if human and human["tone_issue"]["majority"] is True:
        return "technical_tone_error"
    if human and (
        human["initial_issue"]["majority"] is True
        or human["final_issue"]["majority"] is True
    ):
        return "technical_segment_error"
    if mode == CalibrationMode.LEARNER_CORRECT:
        return "learner_acceptable"
    return "other_real"


def _score_distributions(
    runs: list[ProviderRun],
    samples: dict[str, BenchmarkSample],
    consensus: dict[str, dict[str, Any]],
) -> dict[str, dict[str, dict[str, list[float]]]]:
    distributions: dict[str, dict[str, dict[str, list[float]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    for run in runs:
        provider_result = run.normalized_result
        sample = samples.get(run.benchmark_sample_id)
        if not isinstance(provider_result, KnownTargetAssessmentResult) or sample is None:
            continue
        group = _sample_group(sample, consensus.get(sample.sample_id))
        identity = _provider_identity(run)
        for field in ("overall_score", "pronunciation_score", "fluency_score"):
            score = getattr(provider_result, field)
            if score is not None:
                distributions[identity][field][group].append(score)
        for syllable in provider_result.syllables:
            if syllable.tone_score is not None:
                distributions[identity]["tone_score"][group].append(syllable.tone_score)
            for phone in syllable.phones:
                if phone.score is not None:
                    distributions[identity]["phone_score"][group].append(phone.score)
    return {
        identity: {
            field: dict(groups) for field, groups in fields.items()
        }
        for identity, fields in distributions.items()
    }


def _provider_metrics(
    runs: list[ProviderRun],
    samples: dict[str, BenchmarkSample],
    consensus: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    confusion: dict[str, dict[str, Counter[str]]] = defaultdict(
        lambda: defaultdict(Counter)
    )
    for run in runs:
        if run.status != RunStatus.SUCCEEDED or run.request_mode != RequestMode.KNOWN_TARGET:
            continue
        provider_result = run.normalized_result
        sample = samples.get(run.benchmark_sample_id)
        human = consensus.get(run.benchmark_sample_id)
        if (
            not isinstance(provider_result, KnownTargetAssessmentResult)
            or sample is None
            or human is None
            or human["qualifying_native_listener_count"] < 3
            or human["stage_b_count"] < 3
            or human["consensus_class"] == "invalid_sample"
        ):
            continue
        identity = _provider_identity(run)
        mode = calibration_mode(sample)
        produced = human["human_supported_produced_tones"]
        affected_tone_indices = set(human["human_supported_tone_error_indices"])
        any_tone_flag = False
        any_tone_decision = False
        for index, syllable in enumerate(provider_result.syllables):
            expected = _expected_tone(sample, index, syllable.reference_tone)
            detected = _tone(syllable.detected_tone)
            actual = produced.get(str(index))
            matrix_actual = actual or "UNKNOWN"
            matrix_detected = detected or "UNKNOWN"
            confusion[identity][matrix_actual][matrix_detected] += 1
            if detected is not None and expected is not None:
                any_tone_decision = True
                any_tone_flag = any_tone_flag or detected != expected
            human_tone_error = index in affected_tone_indices
            human_tone_acceptable = human["tone_issue"]["majority"] is False
            if human_tone_error:
                if detected is None or expected is None:
                    counters[identity]["tone_error_abstain"] += 1
                else:
                    counters[identity]["tone_error_decisions"] += 1
                    if detected == expected:
                        counters[identity]["tone_detection_false_accept"] += 1
                if actual and actual not in {"UNKNOWN", "INVALID"} and actual != expected:
                    if detected is None:
                        counters[identity]["tone_diagnosis_abstain"] += 1
                    else:
                        counters[identity]["tone_diagnosis_decisions"] += 1
                        if detected == expected:
                            counters[identity]["tone_diagnosis_false_accept"] += 1
            elif human_tone_acceptable and detected is not None and expected is not None:
                counters[identity]["acceptable_tone_decisions"] += 1
                if detected != expected:
                    counters[identity]["acceptable_tone_false_reject"] += 1

        if mode == CalibrationMode.NATIVE_CONTROL and any_tone_decision:
            counters[identity]["native_tone_decisions"] += 1
            if any_tone_flag:
                counters[identity]["native_tone_false_reject"] += 1
        if mode == CalibrationMode.LEARNER_CORRECT and any_tone_decision:
            counters[identity]["learner_correct_tone_decisions"] += 1
            if any_tone_flag:
                counters[identity]["learner_correct_tone_false_reject"] += 1

        classifications = {
            classification.lower()
            for syllable in provider_result.syllables
            for classification in syllable.error_classifications
        }
        for syllable in provider_result.syllables:
            classifications.update(
                phone.error_classification.lower()
                for phone in syllable.phones
                if phone.error_classification
            )
        for dimension in ("initial", "final"):
            if human[f"{dimension}_issue"]["majority"] is True:
                counters[identity][f"{dimension}_error_decisions"] += 1
                if not any(dimension in classification for classification in classifications):
                    counters[identity][f"{dimension}_false_accept"] += 1

        if severity_is_severe(
            human.get("semantic_severity"), human.get("consensus_class")
        ):
            counters[identity]["severe_samples"] += 1

    identities = sorted(set(counters) | set(confusion))
    metrics: dict[str, Any] = {}
    for identity in identities:
        count = counters[identity]
        metrics[identity] = {
            "tone_detection_false_acceptance": rate_estimate(
                count["tone_detection_false_accept"], count["tone_error_decisions"]
            ).normalized(),
            "tone_error_abstentions": count["tone_error_abstain"],
            "tone_diagnosis_false_acceptance": rate_estimate(
                count["tone_diagnosis_false_accept"], count["tone_diagnosis_decisions"]
            ).normalized(),
            "tone_diagnosis_abstentions": count["tone_diagnosis_abstain"],
            "native_tone_false_rejection": rate_estimate(
                count["native_tone_false_reject"], count["native_tone_decisions"]
            ).normalized(),
            "learner_correct_tone_false_rejection": rate_estimate(
                count["learner_correct_tone_false_reject"],
                count["learner_correct_tone_decisions"],
            ).normalized(),
            "acceptable_tone_false_rejection": rate_estimate(
                count["acceptable_tone_false_reject"],
                count["acceptable_tone_decisions"],
            ).normalized(),
            "initial_false_acceptance": rate_estimate(
                count["initial_false_accept"], count["initial_error_decisions"]
            ).normalized(),
            "final_false_acceptance": rate_estimate(
                count["final_false_accept"], count["final_error_decisions"]
            ).normalized(),
            "severe_pronunciation_false_acceptance": {
                "numerator": 0,
                "denominator": count["severe_samples"],
                "fraction": None,
                "reason": "Requires a selected score/reassurance policy; none is promoted.",
            },
            "tone_confusion_human_vs_provider": {
                actual: dict(detected)
                for actual, detected in confusion[identity].items()
            },
        }
    return metrics


def _threshold_search(
    runs: list[ProviderRun],
    samples: dict[str, BenchmarkSample],
    consensus: dict[str, dict[str, Any]],
    split: CalibrationSplitManifest | None,
) -> dict[str, Any]:
    observations: dict[str, list[BinaryObservation]] = defaultdict(list)
    for run in runs:
        result = run.normalized_result
        sample = samples.get(run.benchmark_sample_id)
        human = consensus.get(run.benchmark_sample_id)
        if (
            not isinstance(result, KnownTargetAssessmentResult)
            or sample is None
            or human is None
            or human["qualifying_native_listener_count"] < 3
            or human["stage_b_count"] < 3
        ):
            continue
        majority = human["tone_issue"]["majority"]
        affected_tone_indices = set(human["human_supported_tone_error_indices"])
        if majority is None or human["consensus_class"] == "invalid_sample":
            continue
        identity = _provider_identity(run)
        technical_error = any(
            human[f"{dimension}_issue"]["majority"] is True
            for dimension in ("tone", "initial", "final")
        )
        for field in ("pronunciation_score", "overall_score"):
            score = getattr(result, field)
            if score is not None:
                observations[f"{identity}:{field}"].append(
                    BinaryObservation(sample.sample_id, score, technical_error)
                )
        for index, syllable in enumerate(result.syllables):
            if syllable.tone_score is not None:
                if majority is True and index not in affected_tone_indices:
                    continue
                observations[f"{identity}:tone_score"].append(
                    BinaryObservation(
                        sample.sample_id,
                        syllable.tone_score,
                        index in affected_tone_indices,
                    )
                )
        phone_scores = [
            phone.score
            for syllable in result.syllables
            for phone in syllable.phones
            if phone.score is not None
        ]
        segment_error = (
            human["initial_issue"]["majority"] is True
            or human["final_issue"]["majority"] is True
        )
        if phone_scores:
            observations[f"{identity}:minimum_phone_score"].append(
                BinaryObservation(sample.sample_id, min(phone_scores), segment_error)
            )
    candidates = {
        identity: {
            "selection_policy": "No automatic winner; inspect conservative calibration results.",
            "candidates": explore_thresholds(items, split=split),
        }
        for identity, items in observations.items()
    }
    candidates["_unsupported_signals"] = {
        "provider_error_confidence": (
            "Preserved in raw provider detail, but vendors expose different polarity/scales and "
            "missing-on-correct behavior. Define a provider-specific acceptance signal before "
            "threshold exploration; do not coerce it into a universal score."
        )
    }
    return candidates


def _provider_summary(runs: list[ProviderRun]) -> dict[str, Any]:
    grouped: dict[str, list[ProviderRun]] = defaultdict(list)
    for run in runs:
        grouped[_provider_identity(run)].append(run)
    return {
        identity: {
            "live_run_count": sum(
                run.status == RunStatus.SUCCEEDED
                and run.evidence_origin
                in {EvidenceOrigin.LIVE_PROVIDER, EvidenceOrigin.LIVE_CAPTURED_SANITIZED}
                for run in provider_runs
            ),
            "successes": sum(run.status == RunStatus.SUCCEEDED for run in provider_runs),
            "failures": sum(run.status == RunStatus.FAILED for run in provider_runs),
            "p50_latency_seconds": quantile(
                [
                    run.response_latency_seconds
                    for run in provider_runs
                    if run.response_latency_seconds is not None
                ],
                0.5,
            ),
            "p95_latency_seconds": quantile(
                [
                    run.response_latency_seconds
                    for run in provider_runs
                    if run.response_latency_seconds is not None
                ],
                0.95,
            ),
            "estimated_cost_usd": sum(
                run.estimated_cost_usd or 0 for run in provider_runs
            ),
            "modes": sorted(
                {
                    json.dumps(run.request_configuration, sort_keys=True, ensure_ascii=False)
                    for run in provider_runs
                }
            ),
        }
        for identity, provider_runs in sorted(grouped.items())
    }


def _acoustic_provider_agreement(
    runs: list[ProviderRun],
    samples: dict[str, BenchmarkSample],
    consensus: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    acoustics: dict[str, list[tuple[str, AcousticAnalysisResult]]] = defaultdict(list)
    providers: dict[str, list[tuple[str, KnownTargetAssessmentResult]]] = defaultdict(list)
    for run in runs:
        if isinstance(run.normalized_result, AcousticAnalysisResult):
            acoustics[run.benchmark_sample_id].append(
                (_provider_identity(run), run.normalized_result)
            )
        elif isinstance(run.normalized_result, KnownTargetAssessmentResult):
            providers[run.benchmark_sample_id].append(
                (_provider_identity(run), run.normalized_result)
            )
    counts: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    directions = {1: "level", 2: "rising", 4: "falling"}
    for sample_id in sorted(set(acoustics) & set(providers)):
        sample = samples.get(sample_id)
        human = consensus.get(sample_id)
        if sample is None or len(sample.intended_pinyin) != 1:
            continue
        for provider_identity, provider_result in providers[sample_id]:
            syllable = provider_result.syllables[0] if provider_result.syllables else None
            provider_tone = _tone(syllable.detected_tone) if syllable else None
            expected = _expected_tone(
                sample, 0, syllable.reference_tone if syllable else None
            )
            for acoustic_identity, acoustic_result in acoustics[sample_id]:
                slope = acoustic_result.contour_features.get("start_end_slope_st_per_s")
                f0_direction = (
                    "rising"
                    if slope is not None and slope > 0
                    else "falling"
                    if slope is not None and slope < 0
                    else "level"
                    if slope == 0
                    else None
                )
                numeric_provider = (
                    int(provider_tone[1:])
                    if provider_tone and provider_tone[1:].isdigit()
                    else None
                )
                numeric_expected = (
                    int(expected[1:])
                    if expected and expected[1:].isdigit()
                    else None
                )
                if provider_tone is None and f0_direction is None:
                    classification = "both_unavailable"
                elif provider_tone is None:
                    classification = "provider_tone_unavailable"
                elif f0_direction is None:
                    classification = "f0_unavailable"
                elif (
                    numeric_provider is not None
                    and directions.get(numeric_provider) == f0_direction
                ):
                    classification = "provider_agrees_with_f0"
                else:
                    classification = "provider_conflicts_with_f0"
                counts[classification] += 1
                rows.append(
                    {
                        "sample_id": sample_id,
                        "provider": provider_identity,
                        "acoustic": acoustic_identity,
                        "expected_surface_tone": expected,
                        "provider_tone": provider_tone,
                        "f0_direction": f0_direction,
                        "classification": classification,
                        "human_tone_error": (
                            0 in human["human_supported_tone_error_indices"]
                            if human
                            and human["qualifying_native_listener_count"] >= 3
                            else None
                        ),
                        "provider_matches_expected": (
                            numeric_provider == numeric_expected
                            if numeric_provider is not None and numeric_expected is not None
                            else None
                        ),
                    }
                )
    return {
        "counts": dict(counts),
        "comparisons": rows,
        "promotion_state": "exploratory_only",
        "warning": "F0 conflict is evidence conflict, not acoustic ground truth.",
    }


def _git_commit() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return "undocumented"
    return completed.stdout.strip() or "undocumented"


def _raw_hash(run: ProviderRun) -> str:
    if run.raw_response_sha256:
        return run.raw_response_sha256
    encoded = json.dumps(run.raw_response, sort_keys=True, ensure_ascii=False, default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def generate_pronunciation_calibration(
    *,
    manifest_path: Path,
    runs_dir: Path,
    annotations_dir: Path,
    output_dir: Path,
    split_path: Path | None = None,
) -> dict[str, Any]:
    manifest = load_model(manifest_path, CorpusManifest)
    recorded = [
        sample
        for sample in manifest.samples
        if sample.audio is not None
        and sample.speaker_category != SpeakerCategory.SYNTHETIC_REFERENCE
    ]
    samples = {sample.sample_id: sample for sample in recorded}
    all_runs = _runs(runs_dir)
    qualifying_runs = [
        run
        for run in all_runs
        if run.benchmark_sample_id in samples and _real_run(run)
    ]
    runs, superseded_run_ids = _latest_evidence_runs(qualifying_runs)
    annotations = [
        item for item in _annotations(annotations_dir) if item.blind.sample_id in samples
    ]
    consensus = _human_consensus(samples, annotations)
    mode_counts = Counter(
        mode.value
        for sample in recorded
        if (mode := calibration_mode(sample)) is not None
    )
    deliberate_errors = sum(
        mode_counts[mode.value]
        for mode in (
            CalibrationMode.LEARNER_INTENTIONAL_TONE_ERROR,
            CalibrationMode.LEARNER_INTENTIONAL_INITIAL_ERROR,
            CalibrationMode.LEARNER_INTENTIONAL_FINAL_ERROR,
        )
    )
    critical = [
        sample
        for sample in recorded
        if calibration_mode(sample)
        in {
            CalibrationMode.LEARNER_INTENTIONAL_TONE_ERROR,
            CalibrationMode.LEARNER_INTENTIONAL_INITIAL_ERROR,
            CalibrationMode.LEARNER_INTENTIONAL_FINAL_ERROR,
        }
    ]
    critical_with_three = sum(
        consensus.get(sample.sample_id, {}).get("qualifying_native_listener_count", 0) >= 3
        and consensus.get(sample.sample_id, {}).get("stage_b_count", 0) >= 3
        for sample in critical
    )
    human_tone_errors = sum(
        len(item["human_supported_tone_error_indices"])
        for item in consensus.values()
        if item["qualifying_native_listener_count"] >= 3
        and item["stage_b_count"] >= 3
        and item["consensus_class"] != "invalid_sample"
    )
    human_acceptable_tones = sum(
        len(samples[sample_id].intended_pinyin)
        for sample_id, item in consensus.items()
        if item["qualifying_native_listener_count"] >= 3
        and item["stage_b_count"] >= 3
        and item["tone_issue"]["majority"] is False
        and item["consensus_class"] != "invalid_sample"
    )
    split = (
        load_model(split_path, CalibrationSplitManifest)
        if split_path is not None and split_path.exists()
        else None
    )
    held_out_ready = split is not None and bool(split.held_out_sample_ids)
    minimum_gates = {
        "learner_deliberate_errors": {
            "ready": deliberate_errors >= 30,
            "actual": deliberate_errors,
            "required": 30,
        },
        "tone_errors": {
            "ready": mode_counts[CalibrationMode.LEARNER_INTENTIONAL_TONE_ERROR.value] >= 10,
            "actual": mode_counts[CalibrationMode.LEARNER_INTENTIONAL_TONE_ERROR.value],
            "required": 10,
        },
        "initial_errors": {
            "ready": mode_counts[CalibrationMode.LEARNER_INTENTIONAL_INITIAL_ERROR.value] >= 10,
            "actual": mode_counts[CalibrationMode.LEARNER_INTENTIONAL_INITIAL_ERROR.value],
            "required": 10,
        },
        "final_errors": {
            "ready": mode_counts[CalibrationMode.LEARNER_INTENTIONAL_FINAL_ERROR.value] >= 10,
            "actual": mode_counts[CalibrationMode.LEARNER_INTENTIONAL_FINAL_ERROR.value],
            "required": 10,
        },
        "native_controls": {
            "ready": mode_counts[CalibrationMode.NATIVE_CONTROL.value] >= 10,
            "actual": mode_counts[CalibrationMode.NATIVE_CONTROL.value],
            "required": 10,
        },
        "negative_controls": {
            "ready": mode_counts[CalibrationMode.NEGATIVE_CONTROL.value] >= 10,
            "actual": mode_counts[CalibrationMode.NEGATIVE_CONTROL.value],
            "required": 10,
        },
        "three_native_listeners_per_critical_sample": {
            "ready": bool(critical) and critical_with_three == len(critical),
            "actual": critical_with_three,
            "required": len(critical) if critical else 30,
        },
    }
    stronger_gates = {
        **minimum_gates,
        "learner_correct_controls": {
            "ready": mode_counts[CalibrationMode.LEARNER_CORRECT.value] >= 12,
            "actual": mode_counts[CalibrationMode.LEARNER_CORRECT.value],
            "required": 12,
        },
    }
    categorical_tone_gates = {
        "human_supported_tone_error_syllables": {
            "ready": human_tone_errors >= 20,
            "actual": human_tone_errors,
            "required": 20,
        },
        "human_supported_acceptable_tone_syllables": {
            "ready": human_acceptable_tones >= 20,
            "actual": human_acceptable_tones,
            "required": 20,
        },
        "critical_rater_coverage": minimum_gates[
            "three_native_listeners_per_critical_sample"
        ],
        "held_out_evaluation": {
            "ready": held_out_ready,
            "actual": len(split.held_out_sample_ids) if split else 0,
            "required": ">=1 persisted held-out partition",
        },
        "held_out_validated_threshold": {
            "ready": False,
            "actual": 0,
            "required": "explicit promotion decision after holdout review",
        },
    }
    provider_metrics = _provider_metrics(runs, samples, consensus)
    threshold_search = _threshold_search(runs, samples, consensus, split)
    maturity = (
        CalibrationMaturity.EXPERIMENTAL
        if runs or any(item["qualifying_native_listener_count"] for item in consensus.values())
        else CalibrationMaturity.RAW_EVIDENCE
    )
    scope = CalibrationScope.NONE
    summary: dict[str, Any] = {
        "data_status": "real_only",
        "benchmark_version": manifest.corpus_version,
        "calibration_maturity": maturity.value,
        "calibration_scope": scope.value,
        "calibration_ready": all(item["ready"] for item in minimum_gates.values()),
        "stronger_paired_pilot_ready": all(item["ready"] for item in stronger_gates.values()),
        "categorical_tone_judgment_allowed": False,
        "categorical_tone_judgment_reason": (
            "No threshold has satisfied real-data, three-rater, calibration-selection, and "
            "held-out promotion gates."
        ),
        "counts": {
            "real_recordings": len(recorded),
            "learner_correct": mode_counts[CalibrationMode.LEARNER_CORRECT.value],
            "tone_errors": mode_counts[
                CalibrationMode.LEARNER_INTENTIONAL_TONE_ERROR.value
            ],
            "initial_errors": mode_counts[
                CalibrationMode.LEARNER_INTENTIONAL_INITIAL_ERROR.value
            ],
            "final_errors": mode_counts[
                CalibrationMode.LEARNER_INTENTIONAL_FINAL_ERROR.value
            ],
            "native_controls": mode_counts[CalibrationMode.NATIVE_CONTROL.value],
            "negative_controls": mode_counts[CalibrationMode.NEGATIVE_CONTROL.value],
            "spontaneous_samples": mode_counts[CalibrationMode.SPONTANEOUS_NATURAL.value],
            "unique_native_raters": len(
                {
                    item.blind.listener_id
                    for item in annotations
                    if item.blind.rater_profile
                    and item.blind.rater_profile.native_mandarin_self_report
                }
            ),
            "stage_a_annotations": len(annotations),
            "stage_b_annotations": sum(item.revealed is not None for item in annotations),
            "samples_with_three_native_raters": sum(
                item["qualifying_native_listener_count"] >= 3 for item in consensus.values()
            ),
            "known_target_provider_runs": len(runs),
        },
        "audio_quality_exclusions": [
            sample.sample_id
            for sample in recorded
            if sample.recording_quality and sample.recording_quality.status == "invalid"
        ],
        "gates": minimum_gates,
        "gate_sets": {
            "minimum_existing_pilot": minimum_gates,
            "stronger_paired_pilot": stronger_gates,
            "categorical_tone": categorical_tone_gates,
        },
        "split": split.model_dump(mode="json") if split else None,
        "human_consensus": consensus,
        "human_evidence_summary": _human_evidence_summary(consensus, annotations),
        "provider_metrics": provider_metrics,
        "superseded_provider_run_ids": sorted(superseded_run_ids),
        "score_distributions": _score_distributions(runs, samples, consensus),
        "threshold_search": threshold_search,
        "providers": _provider_summary(runs),
        "provider_status_scorecard": provider_status_scorecard(runs),
        "acoustics": {
            "real_comparison_status": (
                "not_run" if not recorded else "tooling_pending_manual_review"
            ),
            "production_decision": "keep_autocorrelation_pending_real_comparison",
            "provider_agreement": _acoustic_provider_agreement(runs, samples, consensus),
        },
        "alignment": {
            "real_comparison_status": "not_run" if not recorded else "pending_manual_review",
            "production_strategy": "provider_timing_and_MFA_remain_provenance-separated",
        },
        "warning": (
            "Synthetic replay, constructed fixtures, documentation examples, and TTS are excluded "
            "from every headline count and metric. Requested learner error is not ground truth."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "pronunciation-calibration.json", summary)
    run_manifest = CalibrationRunManifest(
        benchmark_version=manifest.corpus_version,
        git_commit_sha=_git_commit(),
        provider_adapter_versions={
            _provider_identity(run): run.adapter_version for run in runs
        },
        provider_configurations={
            _provider_identity(run): run.request_configuration for run in runs
        },
        included_sample_ids=tuple(sorted(samples)),
        excluded_sample_ids=tuple(
            sorted(
                sample.sample_id
                for sample in manifest.samples
                if sample.sample_id not in samples
            )
        ),
        human_annotation_version="two-stage-v2-native-profile",
        split_version=split.split_version if split else None,
    )
    write_model(output_dir / "pronunciation-calibration.manifest.json", run_manifest)
    if runs:
        write_json(
            output_dir / "pronunciation-provider-raw-hashes.json",
            {run.run_id: _raw_hash(run) for run in runs},
        )
    lines = [
        "# Pronunciation calibration",
        "",
        "**NOT READY**"
        if not summary["categorical_tone_judgment_allowed"]
        else "**NARROW CALIBRATION READY**",
        "",
        summary["warning"],
        "",
        f"Maturity: `{maturity.value}`. Scope: `{scope.value}`.",
        "",
        "## Real corpus and human evidence",
        "",
        "| Evidence | Count |",
        "|---|---:|",
    ]
    for name, value in summary["counts"].items():
        lines.append(f"| {name.replace('_', ' ')} | {value} |")
    lines.extend(["", "## Readiness gates", ""])
    for section, gates in summary["gate_sets"].items():
        lines.extend(
            [
                f"### {section.replace('_', ' ').title()}",
                "",
                "| Gate | Actual | Required | State |",
                "|---|---:|---:|---|",
            ]
        )
        for name, gate in gates.items():
            lines.append(
                f"| {name.replace('_', ' ')} | {gate['actual']} | {gate['required']} | "
                f"{'READY' if gate['ready'] else 'NOT READY'} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Provider evidence",
            "",
            (
                "No qualifying real provider runs exist. Fixture parsing is not live validation."
                if not runs
                else "Provider metrics, counts, confidence intervals, abstentions, score overlap, "
                "and exploratory thresholds are in the JSON artifact."
            ),
            "",
            "| Provider/mode | Lifecycle | Live runs | Calibration |",
            "|---|---|---:|---|",
        ]
    )
    for row in summary["provider_status_scorecard"]:
        lines.append(
            f"| {row['provider']} / {row['mode']} | {row['lifecycle']} | "
            f"{row['observed_live_run_count']} | {row['calibration_maturity']} / "
            f"{row['calibration_scope']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Categorical pronunciation calibration remains incomplete.",
            "",
            "Categorical tone judgment remains disabled. "
            + summary["categorical_tone_judgment_reason"],
            "",
        ]
    )
    (output_dir / "pronunciation-calibration.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return summary

"""Real-only pronunciation calibration report and readiness gates."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from benchmark.annotations import load_annotation
from benchmark.models import (
    BenchmarkSample,
    CorpusManifest,
    ErrorType,
    HumanListenerAnnotation,
    KnownTargetAssessmentResult,
    ProviderRun,
    RequestMode,
    RunStatus,
    SpeakerCategory,
)
from benchmark.storage import load_model, write_json


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


def _tone(value: str | None) -> str | None:
    if value is None:
        return None
    digits = [item for item in value if item in "012345"]
    if not digits:
        return None
    return "T0" if digits[-1] == "5" else f"T{digits[-1]}"


def _human_consensus(
    samples: dict[str, BenchmarkSample], annotations: list[HumanListenerAnnotation]
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[HumanListenerAnnotation]] = defaultdict(list)
    for annotation in annotations:
        grouped[annotation.blind.sample_id].append(annotation)
    result: dict[str, dict[str, Any]] = {}
    for sample_id, items in grouped.items():
        if sample_id not in samples:
            continue
        revealed = [item.revealed for item in items if item.revealed is not None]
        result[sample_id] = {
            "listener_count": len(items),
            "understood_first_pass": {
                "yes": sum(item.blind.response.understood_first_pass for item in items),
                "total": len(items),
            },
            "would_request_repetition": {
                "yes": sum(item.blind.response.would_request_repetition for item in items),
                "total": len(items),
            },
            "tone_issue": {
                "yes": sum(item.response.tone_problem for item in revealed),
                "total": len(revealed),
            },
            "initial_issue": {
                "yes": sum(item.response.initial_problem for item in revealed),
                "total": len(revealed),
            },
            "final_issue": {
                "yes": sum(item.response.final_problem for item in revealed),
                "total": len(revealed),
            },
            "individual_annotations": [item.model_dump(mode="json") for item in items],
        }
    return result


def _score_distributions(
    runs: list[ProviderRun], samples: dict[str, BenchmarkSample]
) -> dict[str, dict[str, list[float]]]:
    distributions: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for run in runs:
        result = run.normalized_result
        sample = samples.get(run.benchmark_sample_id)
        if not isinstance(result, KnownTargetAssessmentResult) or sample is None:
            continue
        score = (
            result.pronunciation_score
            if result.pronunciation_score is not None
            else result.overall_score
        )
        if score is None:
            continue
        group = (
            "native_control"
            if sample.speaker_category == SpeakerCategory.NATIVE_CONTROL
            else "meaningful_error"
            if sample.deliberate_error
            and sample.deliberate_error.error_type != ErrorType.NONE
            else "acceptable_learner"
        )
        distributions[run.provider][group].append(score)
    return {
        provider: {group: values for group, values in groups.items()}
        for provider, groups in distributions.items()
    }


def _tone_metrics(
    runs: list[ProviderRun],
    samples: dict[str, BenchmarkSample],
    consensus: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    confusion: dict[str, dict[str, Counter[str]]] = defaultdict(
        lambda: defaultdict(Counter)
    )
    false_accept: dict[str, list[bool]] = defaultdict(list)
    false_reject: dict[str, list[bool]] = defaultdict(list)
    detection: dict[str, list[bool]] = defaultdict(list)
    diagnosis: dict[str, list[bool]] = defaultdict(list)
    for run in runs:
        if run.status != RunStatus.SUCCEEDED or run.request_mode != RequestMode.KNOWN_TARGET:
            continue
        result = run.normalized_result
        sample = samples.get(run.benchmark_sample_id)
        if not isinstance(result, KnownTargetAssessmentResult) or sample is None:
            continue
        for index, syllable in enumerate(result.syllables):
            actual = None
            error = sample.deliberate_error
            if (
                error is not None
                and error.error_type == ErrorType.WRONG_TONE
                and error.corrupted_syllable_index == index
            ):
                actual = _tone(error.produced_form)
            if actual is None and index < len(sample.expected_surface_tones):
                actual = _tone(sample.expected_surface_tones[index])
            detected = _tone(syllable.detected_tone)
            if actual and detected:
                confusion[run.provider][actual][detected] += 1
        human = consensus.get(sample.sample_id)
        error = sample.deliberate_error
        if error and error.error_type == ErrorType.WRONG_TONE and human:
            tone_vote = human["tone_issue"]
            meaningful = tone_vote["total"] >= 3 and tone_vote["yes"] >= 2
            corrupted_index = error.corrupted_syllable_index
            evaluated_syllable = (
                result.syllables[corrupted_index]
                if corrupted_index is not None and corrupted_index < len(result.syllables)
                else None
            )
            expected = (
                _tone(sample.expected_surface_tones[corrupted_index])
                if corrupted_index is not None
                and corrupted_index < len(sample.expected_surface_tones)
                else None
            )
            detected = _tone(evaluated_syllable.detected_tone) if evaluated_syllable else None
            actual = _tone(error.produced_form)
            if meaningful and detected is not None and expected is not None:
                false_accept[run.provider].append(detected == expected)
                detection[run.provider].append(detected != expected)
                if actual is not None:
                    diagnosis[run.provider].append(detected == actual)
        if sample.speaker_category == SpeakerCategory.NATIVE_CONTROL:
            mismatches: list[bool] = []
            for index, item in enumerate(result.syllables):
                expected = (
                    _tone(sample.expected_surface_tones[index])
                    if index < len(sample.expected_surface_tones)
                    else _tone(item.reference_tone)
                )
                detected = _tone(item.detected_tone)
                if detected is not None and expected is not None:
                    mismatches.append(detected != expected)
            if mismatches:
                false_reject[run.provider].append(any(mismatches))

    providers = sorted(
        set(confusion) | set(false_accept) | set(false_reject) | set(detection) | set(diagnosis)
    )

    def rate(values: list[bool]) -> float | None:
        return sum(values) / len(values) if values else None

    return {
        "by_provider": {
            provider: {
                "tone_false_acceptance": rate(false_accept[provider]),
                "tone_false_acceptance_n": len(false_accept[provider]),
                "native_tone_false_rejection": rate(false_reject[provider]),
                "native_tone_false_rejection_n": len(false_reject[provider]),
                "tone_error_detection": rate(detection[provider]),
                "tone_error_detection_n": len(detection[provider]),
                "tone_diagnosis": rate(diagnosis[provider]),
                "tone_diagnosis_n": len(diagnosis[provider]),
                "tone_confusion": {
                    actual: dict(detected)
                    for actual, detected in confusion[provider].items()
                },
            }
            for provider in providers
        },
        "method": (
            "Rates require provider tone hypotheses and at least three listener annotations. "
            "No provider-score threshold is selected."
        ),
    }


def generate_pronunciation_calibration(
    *, manifest_path: Path, runs_dir: Path, annotations_dir: Path, output_dir: Path
) -> dict[str, Any]:
    manifest = load_model(manifest_path, CorpusManifest)
    recorded = [
        sample
        for sample in manifest.samples
        if sample.audio is not None
        and sample.speaker_category != SpeakerCategory.SYNTHETIC_REFERENCE
    ]
    samples = {sample.sample_id: sample for sample in recorded}
    runs = [
        run
        for run in _runs(runs_dir)
        if run.benchmark_sample_id in samples
        and not (
            isinstance(run.raw_response, dict)
            and (run.raw_response.get("synthetic") or run.raw_response.get("fixture"))
        )
    ]
    annotations = [
        item for item in _annotations(annotations_dir) if item.blind.sample_id in samples
    ]
    consensus = _human_consensus(samples, annotations)
    error_counts = Counter(
        sample.deliberate_error.error_type.value
        for sample in recorded
        if sample.deliberate_error
        and sample.deliberate_error.error_type != ErrorType.NONE
    )
    learner_errors = sum(
        error_counts[item]
        for item in ("wrong_tone", "wrong_initial", "wrong_final")
    )
    native_controls = sum(
        sample.speaker_category == SpeakerCategory.NATIVE_CONTROL for sample in recorded
    )
    negative_controls = sum(
        bool({"negative_control", "nonsense", "low_confidence"} & sample.tags)
        for sample in recorded
    )
    critical = [
        sample
        for sample in recorded
        if sample.deliberate_error
        and sample.deliberate_error.error_type
        in {ErrorType.WRONG_TONE, ErrorType.WRONG_INITIAL, ErrorType.WRONG_FINAL}
    ]
    fully_annotated = sum(
        consensus.get(sample.sample_id, {}).get("listener_count", 0) >= 3
        for sample in critical
    )
    gates = {
        "learner_deliberate_errors": {
            "ready": learner_errors >= 30,
            "actual": learner_errors,
            "required": 30,
        },
        "tone_errors": {
            "ready": error_counts["wrong_tone"] >= 10,
            "actual": error_counts["wrong_tone"],
            "required": 10,
        },
        "initial_errors": {
            "ready": error_counts["wrong_initial"] >= 10,
            "actual": error_counts["wrong_initial"],
            "required": 10,
        },
        "final_errors": {
            "ready": error_counts["wrong_final"] >= 10,
            "actual": error_counts["wrong_final"],
            "required": 10,
        },
        "native_controls": {
            "ready": native_controls >= 10,
            "actual": native_controls,
            "required": 10,
        },
        "negative_controls": {
            "ready": negative_controls >= 10,
            "actual": negative_controls,
            "required": 10,
        },
        "three_listeners_per_critical_sample": {
            "ready": bool(critical) and fully_annotated == len(critical),
            "actual": fully_annotated,
            "required": len(critical) if critical else 30,
        },
    }
    summary: dict[str, Any] = {
        "data_status": "real_only",
        "calibration_ready": all(item["ready"] for item in gates.values()),
        "counts": {
            "real_recordings": len(recorded),
            "real_learner_deliberate_errors": learner_errors,
            "native_controls": native_controls,
            "negative_controls": negative_controls,
            "native_listeners": len({item.blind.listener_id for item in annotations}),
            "annotations": len(annotations),
            "known_target_provider_runs": len(runs),
        },
        "gates": gates,
        "human_consensus": consensus,
        "tone_metrics": _tone_metrics(runs, samples, consensus),
        "score_distributions": _score_distributions(runs, samples),
        "segmental_metrics": {
            "initial_false_acceptance": None,
            "final_false_acceptance": None,
            "overall_false_acceptance": None,
            "reason": "Requires real provider evidence joined to three-listener labels.",
        },
        "unresolved_conflicts": [],
        "warning": "Synthetic/replay fixtures are excluded from every count and metric.",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "pronunciation-calibration.json", summary)
    lines = [
        "# Pronunciation calibration",
        "",
        "**NOT READY**" if not summary["calibration_ready"] else "**PRELIMINARY PILOT READY**",
        "",
        summary["warning"],
        "",
        "## Real data counts",
        "",
        "| Evidence | Actual |",
        "|---|---:|",
    ]
    for name, value in summary["counts"].items():
        lines.append(f"| {name.replace('_', ' ')} | {value} |")
    lines.extend(
        [
            "",
            "## Readiness gates",
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
    lines.extend(
        [
            "",
            "## Calibration results",
            "",
            (
                "Metrics remain unavailable until real evidence and listener gates are met."
                if not runs
                else "See the JSON artifact for per-provider confusion and error metrics."
            ),
            "",
            "Categorical pronunciation calibration remains incomplete."
            if not summary["calibration_ready"]
            else (
                "This small pilot permits only preliminary behavior; "
                "it is not general validation."
            ),
            "",
        ]
    )
    (output_dir / "pronunciation-calibration.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return summary

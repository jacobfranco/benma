"""Generate machine-readable and human-readable benchmark reports."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from benchmark.annotations import load_annotation
from benchmark.evaluation.cost import calculate_scenarios, load_catalog
from benchmark.evaluation.metrics import (
    inter_rater_pairwise_cer,
    known_metrics,
    normalize_transcript,
    unknown_metrics,
)
from benchmark.models import (
    BlindAnnotationCommit,
    CorpusManifest,
    KnownTargetAssessmentResult,
    ProviderRun,
    RequestMode,
    RunStatus,
    UnknownTargetPerceptionResult,
)
from benchmark.storage import load_model, write_json, write_json_text


def _load_runs(path: Path) -> list[ProviderRun]:
    if not path.exists():
        return []
    return [load_model(item, ProviderRun) for item in sorted(path.glob("*.json"))]


def _load_annotations(path: Path) -> list[BlindAnnotationCommit]:
    blind_dir = path / "blind"
    if not blind_dir.exists():
        return []
    result: list[BlindAnnotationCommit] = []
    for blind_path in sorted(blind_dir.glob("*.json")):
        revealed_path = path / "revealed" / blind_path.name
        result.append(load_annotation(blind_path, revealed_path).blind)
    return result


def _percent(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.1%}"


def _seconds(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}s"


def _money(value: float | None) -> str:
    return "n/a" if value is None else f"${value:.6f}"


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _negative_control_examples(
    runs: list[ProviderRun], manifest: CorpusManifest
) -> list[dict[str, object]]:
    samples = {sample.sample_id: sample for sample in manifest.samples}
    examples: list[dict[str, object]] = []
    for run in runs:
        sample = samples.get(run.benchmark_sample_id)
        result = run.normalized_result
        if (
            run.request_mode != RequestMode.UNKNOWN_TARGET
            or sample is None
            or not ({"negative_control", "nonsense"} & sample.tags)
            or not isinstance(result, UnknownTargetPerceptionResult)
        ):
            continue
        examples.append(
            {
                "sample_id": sample.sample_id,
                "provider": run.provider,
                "product": run.product,
                "transcript": result.transcript,
                "confidence": result.confidence,
            }
        )
    return sorted(
        examples,
        key=lambda item: (str(item["sample_id"]), str(item["provider"]), str(item["product"])),
    )


def _known_tone_examples(runs: list[ProviderRun]) -> list[dict[str, object]]:
    examples: list[dict[str, object]] = []
    for run in runs:
        result = run.normalized_result
        if not isinstance(result, KnownTargetAssessmentResult):
            continue
        for index, syllable in enumerate(result.syllables):
            if (
                syllable.reference_tone is None
                and syllable.detected_tone is None
                and syllable.tone_score is None
            ):
                continue
            examples.append(
                {
                    "sample_id": run.benchmark_sample_id,
                    "provider": run.provider,
                    "product": run.product,
                    "syllable_index": index,
                    "expected_tone": syllable.reference_tone,
                    "detected_tone": syllable.detected_tone,
                    "tone_score": syllable.tone_score,
                    "human_judgment": None,
                }
            )
    return sorted(
        examples,
        key=lambda item: (
            str(item["provider"]),
            str(item["product"]),
            str(item["sample_id"]),
            int(str(item["syllable_index"])),
        ),
    )


def _unknown_failure_gallery(
    runs: list[ProviderRun],
    manifest: CorpusManifest,
    annotations: list[BlindAnnotationCommit],
) -> list[dict[str, object]]:
    samples = {sample.sample_id: sample for sample in manifest.samples}
    listeners: dict[str, list[BlindAnnotationCommit]] = {}
    for annotation in annotations:
        listeners.setdefault(annotation.sample_id, []).append(annotation)
    gallery: list[dict[str, object]] = []
    for run in runs:
        if run.request_mode != RequestMode.UNKNOWN_TARGET:
            continue
        sample = samples.get(run.benchmark_sample_id)
        result = run.normalized_result
        if (
            sample is None
            or sample.deliberate_error is None
            or not sample.intended_text
            or not isinstance(result, UnknownTargetPerceptionResult)
        ):
            continue
        listener_texts = [
            item.response.perceived_text for item in listeners.get(sample.sample_id, [])
        ]
        provider_repaired = normalize_transcript(result.transcript) == normalize_transcript(
            sample.intended_text
        )
        listener_confusion = any(
            normalize_transcript(text) != normalize_transcript(sample.intended_text)
            for text in listener_texts
        )
        if provider_repaired and listener_confusion:
            gallery.append(
                {
                    "sample_id": sample.sample_id,
                    "target": sample.intended_text,
                    "deliberate_issue": sample.deliberate_error.model_dump(
                        mode="json", exclude_none=True
                    ),
                    "native_listener_transcripts": listener_texts,
                    "provider": run.provider,
                    "product": run.product,
                    "provider_transcript": result.transcript,
                    "observation": (
                        "Provider returned the target while at least one blind listener did not."
                    ),
                }
            )
    return gallery


def generate_report(
    *,
    manifest_path: Path,
    runs_dir: Path,
    annotations_dir: Path,
    pricing_path: Path,
    capabilities_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    manifest = load_model(manifest_path, CorpusManifest)
    runs = _load_runs(runs_dir)
    annotations = _load_annotations(annotations_dir)
    samples = {sample.sample_id: sample for sample in manifest.samples}
    capabilities = json.loads(capabilities_path.read_text(encoding="utf-8"))
    grouped: dict[tuple[str, str, RequestMode], list[ProviderRun]] = {}
    for run in runs:
        grouped.setdefault((run.provider, run.product, run.request_mode), []).append(run)
    unknown_summary: dict[str, object] = {}
    known_summary: dict[str, object] = {}
    for (provider, product, mode), provider_runs in sorted(grouped.items()):
        suffix = "/context_probe" if mode == RequestMode.CONTEXT_PROBE else ""
        key = f"{provider}/{product}{suffix}"
        if mode in {RequestMode.UNKNOWN_TARGET, RequestMode.CONTEXT_PROBE}:
            unknown_summary[key] = asdict(unknown_metrics(provider_runs, samples, annotations))
        elif mode == RequestMode.KNOWN_TARGET:
            known_summary[key] = asdict(known_metrics(provider_runs, samples))
    costs = calculate_scenarios(load_catalog(pricing_path))
    gallery = _unknown_failure_gallery(runs, manifest, annotations)
    negative_controls = _negative_control_examples(runs, manifest)
    known_tone_examples = _known_tone_examples(runs)
    fixture_only = bool(runs) and all(
        bool(run.request_configuration.get("replay_fixture")) for run in runs
    )
    timestamps = sorted(run.timestamp.isoformat() for run in runs)
    summary: dict[str, object] = {
        "schema_version": "1.0.0",
        "data_status": "replay_fixture_only" if fixture_only else "contains_live_or_external_runs",
        "report_timestamp": timestamps[-1] if timestamps else None,
        "corpus": {
            "version": manifest.corpus_version,
            "defined_samples": len(manifest.samples),
            "desired_samples": manifest.desired_sample_count,
            "recorded_samples": sum(sample.audio is not None for sample in manifest.samples),
        },
        "runs": {
            "total": len(runs),
            "succeeded": sum(run.status == RunStatus.SUCCEEDED for run in runs),
            "failed": sum(run.status == RunStatus.FAILED for run in runs),
        },
        "human_annotations": {
            "blind_commits": len(annotations),
            "inter_rater_pairwise_cer": inter_rater_pairwise_cer(annotations),
        },
        "unknown_target": unknown_summary,
        "known_target": known_summary,
        "negative_control_examples": negative_controls,
        "known_tone_examples": known_tone_examples,
        "failure_gallery": gallery,
        "provider_capabilities": capabilities,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "comparative.json", summary)
    write_json(output_dir / "cost-scenarios.json", costs)
    _write_runs_csv(output_dir / "runs.csv", runs)
    write_json_text(output_dir / "report.md", _markdown(summary))
    return summary


def _write_runs_csv(path: Path, runs: list[ProviderRun]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "run_id",
                "sample_id",
                "provider",
                "product",
                "mode",
                "status",
                "latency_seconds",
                "audio_duration_seconds",
                "estimated_cost_usd",
                "transcript",
                "overall_score",
                "error_type",
            ],
        )
        writer.writeheader()
        for run in sorted(runs, key=lambda item: item.run_id):
            transcript = ""
            score: float | None = None
            if isinstance(run.normalized_result, UnknownTargetPerceptionResult):
                transcript = run.normalized_result.transcript
            elif isinstance(run.normalized_result, KnownTargetAssessmentResult):
                score = run.normalized_result.overall_score
            writer.writerow(
                {
                    "run_id": run.run_id,
                    "sample_id": run.benchmark_sample_id,
                    "provider": run.provider,
                    "product": run.product,
                    "mode": run.request_mode,
                    "status": run.status,
                    "latency_seconds": run.response_latency_seconds,
                    "audio_duration_seconds": run.audio_duration_seconds,
                    "estimated_cost_usd": run.estimated_cost_usd,
                    "transcript": transcript,
                    "overall_score": score,
                    "error_type": run.error.error_type if run.error else "",
                }
            )


def _markdown(summary: dict[str, object]) -> str:
    corpus = summary["corpus"]
    run_counts = summary["runs"]
    human = summary["human_annotations"]
    assert isinstance(corpus, dict) and isinstance(run_counts, dict) and isinstance(human, dict)
    lines = [
        "# Benma speech benchmark report",
        "",
        f"Data status: **{summary['data_status']}**.",
        "",
        (
            "> Replay fixtures validate the harness; they are not experimental evidence and "
            "must not be used "
        ),
        "> to select a production vendor.",
        "",
        "## Benchmark status",
        "",
        f"- Corpus: {corpus['defined_samples']} defined / {corpus['desired_samples']} desired; "
        f"{corpus['recorded_samples']} recorded",
        f"- Provider runs: {run_counts['total']} total, {run_counts['succeeded']} succeeded, "
        f"{run_counts['failed']} failed",
        f"- Blind listener commits: {human['blind_commits']}",
        f"- Inter-rater pairwise CER: {_percent(human['inter_rater_pairwise_cer'])}",
        "",
        "## Unknown-target perception",
        "",
        (
            "| Provider/product | Success | Target CER / WER | Human CER | Error preservation | "
            "Semantic repair |"
        ),
        "|---|---:|---:|---:|---:|---:|",
    ]
    unknown = summary["unknown_target"]
    assert isinstance(unknown, dict)
    for key, raw in sorted(unknown.items()):
        assert isinstance(raw, dict)
        lines.append(
            f"| {key} | {raw['succeeded']}/{raw['attempted']} | "
            f"{_percent(raw['intended_cer'])} / {_percent(raw['intended_wer'])} | "
            f"{_percent(raw['mean_human_cer'])} | {_percent(raw['error_preservation_recall'])} | "
            f"{_percent(raw['semantic_repair_rate'])} |"
        )
    lines.extend(
        [
            "",
            (
                "Target CER is conventional accuracy and is intentionally not the primary "
                "selection metric."
            ),
            "",
            "### Confidence, context, latency, and fixture cost",
            "",
            (
                "| Provider/product | Confidence n / mean | High-confidence repair | Context "
                "delta | p50 / p95 | Estimated run cost |"
            ),
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for key, raw in sorted(unknown.items()):
        assert isinstance(raw, dict)
        lines.append(
            f"| {key} | {raw['confidence_observations']} / "
            f"{_percent(raw['mean_confidence'])} | "
            f"{_percent(raw['high_confidence_repair_rate'])} | "
            f"{_percent(raw['context_leakage_delta'])} | "
            f"{_seconds(raw['p50_latency_seconds'])} / "
            f"{_seconds(raw['p95_latency_seconds'])} | "
            f"{_money(raw['estimated_cost_usd'])} |"
        )
    lines.extend(
        [
            "",
            (
                "Confidence summaries describe field availability and synthetic-fixture behavior; "
                "they are not calibration evidence."
            ),
            "",
            "## Known-target pronunciation",
            "",
            (
                "| Provider/product | Success | Tone observations | Tone false accept | Native "
                "false reject | Phone / initial / final recall |"
            ),
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    known = summary["known_target"]
    assert isinstance(known, dict)
    for key, raw in sorted(known.items()):
        assert isinstance(raw, dict)
        lines.append(
            f"| {key} | {raw['succeeded']}/{raw['attempted']} | {raw['tone_observations']} | "
            f"{_percent(raw['tone_false_accept_rate'])} | "
            f"{_percent(raw['native_false_reject_rate'])} | "
            f"{_percent(raw['phone_error_recall'])} / "
            f"{_percent(raw['initial_error_recall'])} / "
            f"{_percent(raw['final_error_recall'])} |"
        )
    lines.extend(
        [
            "",
            "### Known-target operations and unavailable capabilities",
            "",
            "| Provider/product | p50 / p95 | Estimated run cost | Explicitly unavailable |",
            "|---|---:|---:|---|",
        ]
    )
    for key, raw in sorted(known.items()):
        assert isinstance(raw, dict)
        unavailable = ", ".join(raw["unsupported_capabilities"]) or "none declared"
        lines.append(
            f"| {key} | {_seconds(raw['p50_latency_seconds'])} / "
            f"{_seconds(raw['p95_latency_seconds'])} | "
            f"{_money(raw['estimated_cost_usd'])} | {_cell(unavailable)} |"
        )
    lines.extend(["", "### Tone confusion matrices", ""])
    confusion_rows = 0
    for key, raw in sorted(known.items()):
        assert isinstance(raw, dict)
        confusion = raw["confusion"]
        assert isinstance(confusion, dict)
        for expected, detected_counts in sorted(confusion.items()):
            assert isinstance(detected_counts, dict)
            for detected, count in sorted(detected_counts.items()):
                if confusion_rows == 0:
                    lines.extend(
                        [
                            "| Provider/product | Expected | Detected | Count |",
                            "|---|---:|---:|---:|",
                        ]
                    )
                lines.append(f"| {key} | {expected} | {detected} | {count} |")
                confusion_rows += 1
    if confusion_rows == 0:
        lines.append("No provider exposed explicit reference/detected tone pairs.")

    tone_examples = summary["known_tone_examples"]
    assert isinstance(tone_examples, list)
    lines.extend(["", "### Tone evidence examples", ""])
    if not tone_examples:
        lines.append("No tone-level evidence is present in the loaded runs.")
    else:
        lines.extend(
            [
                "| Sample | Provider/product | Unit | Expected | Detected | Score | Human |",
                "|---|---|---:|---:|---:|---:|---|",
            ]
        )
        for item in tone_examples:
            assert isinstance(item, dict)
            score = item["tone_score"]
            score_text = "n/a" if score is None else f"{float(score):.1f}"
            human = item["human_judgment"] or "n/a"
            lines.append(
                f"| {_cell(item['sample_id'])} | {item['provider']}/{item['product']} | "
                f"{item['syllable_index']} | {item['expected_tone'] or 'n/a'} | "
                f"{item['detected_tone'] or 'n/a'} | {score_text} | {_cell(human)} |"
            )

    negative_controls = summary["negative_control_examples"]
    assert isinstance(negative_controls, list)
    lines.extend(["", "## Negative/control behavior", ""])
    if not negative_controls:
        lines.append("No negative-control unknown-target run is present in the loaded data.")
    else:
        lines.extend(
            [
                "| Sample | Provider/product | Transcript | Confidence |",
                "|---|---|---|---:|",
            ]
        )
        for item in negative_controls:
            assert isinstance(item, dict)
            transcript = item["transcript"] or "[empty]"
            lines.append(
                f"| {_cell(item['sample_id'])} | {item['provider']}/{item['product']} | "
                f"{_cell(transcript)} | {_percent(item['confidence'])} |"
            )
    gallery = summary["failure_gallery"]
    assert isinstance(gallery, list)
    lines.extend(["", "## Failure gallery", ""])
    if not gallery:
        lines.append("No qualifying semantic-repair case is present in the loaded data.")
    for item in gallery:
        assert isinstance(item, dict)
        lines.extend(
            [
                f"### {item['sample_id']} — {item['provider']}/{item['product']}",
                "",
                f"- Target: {item['target']}",
                f"- Provider: {item['provider_transcript']}",
                f"- Blind listeners: {', '.join(item['native_listener_transcripts'])}",
                f"- Observation: {item['observation']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation",
            "",
            "No provider winner is declared from replay data. Use this report shape only after "
            "collecting "
            "native/learner recordings and blinded native-listener annotations.",
            "",
        ]
    )
    return "\n".join(lines)

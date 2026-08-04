from __future__ import annotations

from datetime import UTC, datetime

from benchmark.corpus.seed import seed_manifest
from benchmark.evaluation.metrics import (
    character_error_rate,
    edit_distance,
    known_metrics,
    normalize_transcript,
    quantile,
    unknown_metrics,
)
from benchmark.models import (
    BlindAnnotationCommit,
    BlindListenerResponse,
    KnownTargetAssessmentResult,
    ProviderRun,
    RequestMode,
    RunStatus,
    SyllableAssessment,
    UnknownTargetPerceptionResult,
)

NOW = datetime(2026, 8, 3, tzinfo=UTC)


def blind(sample_id: str, text: str) -> BlindAnnotationCommit:
    return BlindAnnotationCommit(
        annotation_id=f"ann-{sample_id}",
        sample_id=sample_id,
        listener_id="listener",
        randomized_order=0,
        response=BlindListenerResponse(
            perceived_text=text,
            understood_first_pass=False,
            would_request_repetition=True,
            confidence=0.8,
        ),
        committed_at=NOW,
        commit_sha256="0" * 64,
    )


def run(sample_id: str, transcript: str) -> ProviderRun:
    return ProviderRun(
        run_id=f"run-{sample_id}",
        provider="fixture",
        product="asr",
        adapter_version="1",
        timestamp=NOW,
        benchmark_sample_id=sample_id,
        request_mode=RequestMode.UNKNOWN_TARGET,
        response_latency_seconds=0.5,
        normalized_result=UnknownTargetPerceptionResult(transcript=transcript),
        raw_response={"text": transcript},
        status=RunStatus.SUCCEEDED,
    )


def test_edit_distance_and_normalization() -> None:
    assert edit_distance("北京", "北景") == 1
    assert normalize_transcript(" 北 京。") == "北京"
    assert character_error_rate("北京。", "北景") == 0.5


def test_quantiles_are_interpolated() -> None:
    assert quantile([1.0, 2.0, 3.0, 4.0], 0.5) == 2.5
    assert quantile([], 0.95) is None


def test_semantic_repair_and_preservation_are_separate() -> None:
    sample_id = "sentence_beijing_wrong_tone"
    samples = {sample.sample_id: sample for sample in seed_manifest().samples}
    annotations = [blind(sample_id, "我明天想去背景")]
    repaired = unknown_metrics([run(sample_id, "我明天想去北京")], samples, annotations)
    preserved = unknown_metrics([run(sample_id, "我明天想去背景")], samples, annotations)
    assert repaired.semantic_repair_rate == 1.0
    assert repaired.error_preservation_recall == 0.0
    assert preserved.semantic_repair_rate == 0.0
    assert preserved.error_preservation_recall == 1.0


def test_high_confidence_repair_is_reported_separately() -> None:
    sample_id = "sentence_beijing_wrong_tone"
    samples = {sample.sample_id: sample for sample in seed_manifest().samples}
    confident_run = run(sample_id, "我明天想去北京").model_copy(
        update={
            "normalized_result": UnknownTargetPerceptionResult(
                transcript="我明天想去北京", confidence=0.9
            )
        }
    )
    metrics = unknown_metrics([confident_run], samples, [blind(sample_id, "我明天想去背景")])
    assert metrics.confidence_observations == 1
    assert metrics.mean_confidence == 0.9
    assert metrics.high_confidence_repair_rate == 1.0


def test_no_human_noncanonical_evidence_means_ineligible() -> None:
    sample_id = "sentence_beijing_wrong_tone"
    samples = {sample.sample_id: sample for sample in seed_manifest().samples}
    metrics = unknown_metrics(
        [run(sample_id, "我明天想去北京")], samples, [blind(sample_id, "我明天想去北京")]
    )
    assert metrics.semantic_repair_rate is None


def test_known_tone_scores_remain_uncalibrated_and_confusion_is_reported() -> None:
    samples = {sample.sample_id: sample for sample in seed_manifest().samples}
    sample_id = "sentence_beijing_wrong_tone"
    syllables = tuple(
        SyllableAssessment(
            reference_tone="T3" if index == 3 else None,
            detected_tone="T2" if index == 3 else None,
            tone_score=82 if index == 3 else None,
        )
        for index in range(7)
    )
    provider_run = ProviderRun(
        run_id="known-1",
        provider="fixture",
        product="assessor",
        adapter_version="1",
        timestamp=NOW,
        benchmark_sample_id=sample_id,
        request_mode=RequestMode.KNOWN_TARGET,
        normalized_result=KnownTargetAssessmentResult(syllables=syllables),
        raw_response={},
        status=RunStatus.SUCCEEDED,
    )
    metrics = known_metrics([provider_run], samples)
    assert metrics.tone_false_accept_rate is None
    assert metrics.confusion == {"T3": {"T2": 1}}

"""Deterministic replay evidence that exercises the harness without vendor claims."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from benchmark.annotations import commit_blind
from benchmark.models import (
    BlindListenerResponse,
    ContextCondition,
    EvidenceOrigin,
    KnownTargetAssessmentResult,
    ProviderRun,
    RequestMode,
    RunStatus,
    SyllableAssessment,
    UnknownTargetPerceptionResult,
)
from benchmark.storage import write_model

FIXED_TIME = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)


def materialize_replay_fixtures(root: Path) -> tuple[int, int]:
    runs_dir = root / "runs"
    annotations_root = root / "annotations"
    runs_dir.mkdir(parents=True, exist_ok=True)
    fixture_config = {"replay_fixture": True, "warning": "not experimental evidence"}
    unknown_cases = {
        "sentence_beijing_wrong_tone": {
            "funasr/paraformer-zh": "我明天想去背景",
            "google_cloud/chirp_3": "我明天想去北京",
            "openai/gpt-4o-transcribe": "我明天想去北京",
        },
        "sentence_shuijiao_wrong_initial": {
            "funasr/paraformer-zh": "他吃完饭以后想睡觉",
            "google_cloud/chirp_3": "他吃完饭以后想睡觉",
            "openai/gpt-4o-transcribe": "他吃完饭以后想睡觉",
        },
        "control_nonsense_1": {
            "funasr/paraformer-zh": "嘎咯咪",
            "google_cloud/chirp_3": "咖喱米",
            "openai/gpt-4o-transcribe": "咖喱米",
        },
        "tone_pair_33": {
            "funasr/paraformer-zh": "水果",
            "google_cloud/chirp_3": "水果",
            "openai/gpt-4o-transcribe": "水果",
        },
    }
    run_count = 0
    for sample_index, (sample_id, providers) in enumerate(unknown_cases.items()):
        for provider_index, (key, transcript) in enumerate(providers.items()):
            provider, product = key.split("/", 1)
            confidence = 0.93 - provider_index * 0.04
            raw = {
                "text": transcript,
                "confidence": confidence,
                "fixture": True,
            }
            run = ProviderRun(
                run_id=f"fixture-unknown-{provider}-{sample_id}",
                provider=provider,
                product=product,
                provider_version="fixture",
                adapter_version="1.0.0",
                timestamp=FIXED_TIME + timedelta(seconds=run_count),
                benchmark_sample_id=sample_id,
                request_mode=RequestMode.UNKNOWN_TARGET,
                request_configuration=fixture_config,
                response_latency_seconds=0.21 + sample_index * 0.04 + provider_index * 0.03,
                audio_duration_seconds=2.2,
                estimated_billable_units=2.2 / 60,
                estimated_cost_usd=0.0006 + provider_index * 0.0002,
                normalized_result=UnknownTargetPerceptionResult(
                    transcript=transcript,
                    confidence=confidence,
                    detected_language="zh",
                ),
                raw_response=raw,
                status=RunStatus.SUCCEEDED,
                evidence_origin=EvidenceOrigin.CONSTRUCTED_FIXTURE,
            )
            write_model(runs_dir / f"{run.run_id}.json", run)
            run_count += 1
    context_transcripts = [
        (ContextCondition.NO_CONTEXT, "我明天想去背景", None),
        (ContextCondition.CONGRUENT, "我明天想去北京", "旅行计划提到北京"),
        (ContextCondition.MISLEADING, "我明天想去天津", "旅行计划提到天津"),
    ]
    for condition, transcript, prompt in context_transcripts:
        run = ProviderRun(
            run_id=f"fixture-context-openai-{condition.value}",
            provider="openai",
            product="gpt-4o-transcribe",
            provider_version="fixture",
            adapter_version="1.0.0",
            timestamp=FIXED_TIME + timedelta(seconds=run_count),
            benchmark_sample_id="sentence_beijing_wrong_tone",
            request_mode=RequestMode.CONTEXT_PROBE,
            request_configuration={
                **fixture_config,
                "experimental_prompt": prompt,
                "excluded_from_production_path": True,
            },
            response_latency_seconds=0.3,
            audio_duration_seconds=2.2,
            normalized_result=UnknownTargetPerceptionResult(transcript=transcript),
            raw_response={"text": transcript, "fixture": True},
            status=RunStatus.SUCCEEDED,
            context_condition=condition,
            evidence_origin=EvidenceOrigin.CONSTRUCTED_FIXTURE,
        )
        write_model(runs_dir / f"{run.run_id}.json", run)
        run_count += 1

    known_cases = {
        "isolated_ma2_wrong_as_t3": ("T2", "T3", 42.0, 45.0, 1, 0),
        "sentence_beijing_wrong_tone": ("T3", "T2", 82.0, 35.0, 7, 3),
        "sentence_shuijiao_wrong_initial": (None, None, None, None, 9, 1),
        "isolated_ma1_correct_r1": ("T1", "T1", 94.0, 93.0, 1, 0),
        "tone_pair_33": ("T3", "T3", 90.0, 88.0, 2, 0),
    }
    for sample_index, (
        sample_id,
        (expected, detected, tencent_score, _azure_score, syllable_count, affected_index),
    ) in enumerate(known_cases.items()):
        for provider, product, tone_score in [
            ("tencent", "SOE-N", tencent_score),
            ("azure_speech", "pronunciation_assessment_zh-CN", None),
        ]:
            error_classifications = (
                ("initial_mismatch",)
                if sample_id.endswith("wrong_initial") and provider == "tencent"
                else ()
            )
            syllables = tuple(
                SyllableAssessment(
                    text=f"fixture-unit-{index}",
                    score=58.0 if error_classifications and index == affected_index else 90.0,
                    reference_tone=expected
                    if provider == "tencent" and index == affected_index
                    else None,
                    detected_tone=detected
                    if provider == "tencent" and index == affected_index
                    else None,
                    tone_score=tone_score if index == affected_index else None,
                    error_classifications=(
                        error_classifications if index == affected_index else ()
                    ),
                )
                for index in range(syllable_count)
            )
            normalized = KnownTargetAssessmentResult(
                overall_score=92.0
                if "correct" in sample_id or sample_id == "tone_pair_33"
                else 70.0,
                pronunciation_score=91.0
                if "correct" in sample_id or sample_id == "tone_pair_33"
                else 66.0,
                fluency_score=88.0,
                completeness_score=100.0,
                syllables=syllables,
                unsupported_capabilities=("explicit detected tone",)
                if provider == "azure_speech"
                else (),
            )
            run = ProviderRun(
                run_id=f"fixture-known-{provider}-{sample_id}",
                provider=provider,
                product=product,
                provider_version="fixture",
                adapter_version="1.0.0",
                timestamp=FIXED_TIME + timedelta(seconds=run_count),
                benchmark_sample_id=sample_id,
                request_mode=RequestMode.KNOWN_TARGET,
                request_configuration=fixture_config,
                response_latency_seconds=0.4 + sample_index * 0.05,
                audio_duration_seconds=1.5,
                normalized_result=normalized,
                raw_response={"normalized": normalized.model_dump(mode="json"), "fixture": True},
                status=RunStatus.SUCCEEDED,
                evidence_origin=EvidenceOrigin.CONSTRUCTED_FIXTURE,
            )
            write_model(runs_dir / f"{run.run_id}.json", run)
            run_count += 1

    annotation_cases = [
        ("ann-bg-a", "sentence_beijing_wrong_tone", "listener-a", "我明天想去背景", False, True),
        ("ann-bg-b", "sentence_beijing_wrong_tone", "listener-b", "我明天想去北京", True, False),
        (
            "ann-sj-a",
            "sentence_shuijiao_wrong_initial",
            "listener-a",
            "他吃完饭以后想睡觉",
            True,
            False,
        ),
        (
            "ann-sj-b",
            "sentence_shuijiao_wrong_initial",
            "listener-b",
            "他吃完饭以后想水饺",
            False,
            True,
        ),
        ("ann-ns-a", "control_nonsense_1", "listener-a", "嘎咯咪", False, True),
        ("ann-ns-b", "control_nonsense_1", "listener-b", "不确定", False, True),
    ]
    for order, (annotation_id, sample_id, listener_id, text, understood, repeat) in enumerate(
        annotation_cases
    ):
        blind_path = annotations_root / "blind" / f"{annotation_id}.json"
        if not blind_path.exists():
            commit_blind(
                blind_path,
                annotation_id=annotation_id,
                sample_id=sample_id,
                listener_id=listener_id,
                randomized_order=order,
                response=BlindListenerResponse(
                    perceived_text=text,
                    understood_first_pass=understood,
                    would_request_repetition=repeat,
                    confidence=0.8,
                    notes="Synthetic fixture; not a human research annotation.",
                ),
                now=FIXED_TIME + timedelta(seconds=order),
            )
    return run_count, len(annotation_cases)

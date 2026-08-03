from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from benchmark.corpus.seed import seed_manifest
from benchmark.models import (
    AudioAsset,
    BenchmarkSample,
    CorpusManifest,
    KnownTargetAssessmentRequest,
    ProviderError,
    ProviderRun,
    RequestMode,
    RunStatus,
    SpeakerCategory,
    UnknownTargetPerceptionRequest,
    UnknownTargetPerceptionResult,
)


def test_unknown_request_has_no_target_or_context_fields() -> None:
    fields = UnknownTargetPerceptionRequest.model_fields
    forbidden = {"target", "target_text", "intended_text", "context", "prompt", "pinyin"}
    assert forbidden.isdisjoint(fields)


@pytest.mark.parametrize("field", ["target_text", "intended_text", "context", "prompt"])
def test_unknown_request_rejects_target_leakage(field: str) -> None:
    payload = {
        "sample_id": "sample_1",
        "audio": {"asset_path": "recording.wav"},
        field: "你好",
    }
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        UnknownTargetPerceptionRequest.model_validate(payload)


def test_known_request_requires_and_accepts_target() -> None:
    request = KnownTargetAssessmentRequest(
        sample_id="sample_1",
        audio=AudioAsset(asset_path="recording.wav"),
        target_text="你好",
        target_pinyin=("nǐ", "hǎo"),
    )
    assert request.target_text == "你好"


def test_sample_round_trip() -> None:
    original = seed_manifest().samples[0]
    restored = BenchmarkSample.model_validate_json(original.model_dump_json())
    assert restored == original


def test_sample_rejects_incoherent_tone_lengths() -> None:
    with pytest.raises(ValidationError, match="equal lengths"):
        BenchmarkSample(
            sample_id="bad_sample",
            corpus_version="1",
            speaker_category=SpeakerCategory.LEARNER,
            intended_pinyin=("nǐ", "hǎo"),
            lexical_tones=(3,),
        )


def test_recorded_sample_requires_audio() -> None:
    with pytest.raises(ValidationError, match="require an audio"):
        BenchmarkSample(
            sample_id="bad_sample",
            corpus_version="1",
            speaker_category=SpeakerCategory.LEARNER,
            status="recorded",
        )


def test_manifest_rejects_duplicate_ids() -> None:
    sample = seed_manifest().samples[0]
    with pytest.raises(ValidationError, match="unique"):
        CorpusManifest(
            corpus_id="test",
            corpus_version="1",
            desired_sample_count=2,
            description="test",
            samples=(sample, sample),
        )


def test_provider_run_preserves_raw_response_round_trip() -> None:
    raw = {"nested": {"tokens": [1, 2, 3]}, "vendor_only": "unchanged"}
    run = ProviderRun(
        run_id="run-1",
        provider="fixture",
        product="model",
        adapter_version="1",
        timestamp=datetime(2026, 8, 3, tzinfo=UTC),
        benchmark_sample_id="sample_1",
        request_mode=RequestMode.UNKNOWN_TARGET,
        normalized_result=UnknownTargetPerceptionResult(transcript="你好"),
        raw_response=raw,
        status=RunStatus.SUCCEEDED,
    )
    restored = ProviderRun.model_validate_json(run.model_dump_json())
    assert restored.raw_response == raw


def test_successful_run_requires_normalized_result() -> None:
    with pytest.raises(ValidationError, match="requires normalized_result"):
        ProviderRun(
            run_id="run-1",
            provider="fixture",
            product="model",
            adapter_version="1",
            benchmark_sample_id="sample_1",
            request_mode=RequestMode.UNKNOWN_TARGET,
            status=RunStatus.SUCCEEDED,
        )


def test_failed_run_requires_error() -> None:
    with pytest.raises(ValidationError, match="requires error"):
        ProviderRun(
            run_id="run-1",
            provider="fixture",
            product="model",
            adapter_version="1",
            benchmark_sample_id="sample_1",
            request_mode=RequestMode.UNKNOWN_TARGET,
            status=RunStatus.FAILED,
        )


def test_failed_run_accepts_explicit_error() -> None:
    run = ProviderRun(
        run_id="run-1",
        provider="fixture",
        product="model",
        adapter_version="1",
        benchmark_sample_id="sample_1",
        request_mode=RequestMode.UNKNOWN_TARGET,
        status=RunStatus.FAILED,
        error=ProviderError(error_type="TimeoutError", message="timed out", retryable=True),
    )
    assert run.error and run.error.retryable


def test_schema_version_rejects_unknown_major() -> None:
    with pytest.raises(ValidationError):
        UnknownTargetPerceptionResult(schema_version="2.0.0", transcript="")  # type: ignore[arg-type]

"""Provider-neutral execution and evidence persistence."""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from pydantic import JsonValue

from benchmark.models import (
    BenchmarkSample,
    KnownTargetAssessmentRequest,
    ProviderError,
    ProviderRun,
    RequestMode,
    RunStatus,
)
from benchmark.providers.base import (
    KnownTargetPronunciationProvider,
    ProviderAdapterError,
    UnknownTargetPerceptionProvider,
)
from benchmark.storage import write_model


def _run_id(provider: str, sample_id: str) -> str:
    return f"{provider}-{sample_id}-{uuid.uuid4().hex[:12]}"


def run_unknown_target(
    provider: UnknownTargetPerceptionProvider,
    sample: BenchmarkSample,
    *,
    output_dir: Path | None = None,
    now: datetime | None = None,
) -> ProviderRun:
    request = sample.perception_request()
    started = time.perf_counter()
    raw: object | None = None
    try:
        result, raw = provider.perceive(request)
        run = ProviderRun(
            run_id=_run_id(provider.provider_name, sample.sample_id),
            provider=provider.provider_name,
            product=provider.product_name,
            adapter_version=provider.adapter_version,
            timestamp=now or datetime.now(UTC),
            benchmark_sample_id=sample.sample_id,
            request_mode=RequestMode.UNKNOWN_TARGET,
            request_configuration={"language_hint": request.language_hint},
            response_latency_seconds=time.perf_counter() - started,
            audio_duration_seconds=request.audio.duration_seconds,
            normalized_result=result,
            raw_response=cast(JsonValue, raw),
            status=RunStatus.SUCCEEDED,
        )
    except Exception as exc:
        retryable = isinstance(exc, ProviderAdapterError) and exc.retryable
        code = exc.code if isinstance(exc, ProviderAdapterError) else None
        run = ProviderRun(
            run_id=_run_id(provider.provider_name, sample.sample_id),
            provider=provider.provider_name,
            product=provider.product_name,
            adapter_version=provider.adapter_version,
            timestamp=now or datetime.now(UTC),
            benchmark_sample_id=sample.sample_id,
            request_mode=RequestMode.UNKNOWN_TARGET,
            request_configuration={"language_hint": request.language_hint},
            response_latency_seconds=time.perf_counter() - started,
            audio_duration_seconds=request.audio.duration_seconds,
            raw_response=cast(JsonValue, raw),
            status=RunStatus.FAILED,
            error=ProviderError(
                error_type=type(exc).__name__,
                message=str(exc),
                retryable=retryable,
                provider_code=code,
            ),
        )
    if output_dir is not None:
        write_model(output_dir / f"{run.run_id}.json", run)
    return run


def run_known_target(
    provider: KnownTargetPronunciationProvider,
    sample: BenchmarkSample,
    *,
    output_dir: Path | None = None,
    now: datetime | None = None,
) -> ProviderRun:
    if sample.audio is None or not sample.intended_text:
        raise ValueError("known-target execution needs recorded audio and intended text")
    request = KnownTargetAssessmentRequest(
        sample_id=sample.sample_id,
        audio=sample.audio,
        target_text=sample.intended_text,
        target_pinyin=sample.intended_pinyin,
        lexical_tones=sample.lexical_tones,
        expected_surface_tones=sample.expected_surface_tones,
    )
    started = time.perf_counter()
    raw: object | None = None
    try:
        result, raw = provider.assess(request)
        run = ProviderRun(
            run_id=_run_id(provider.provider_name, sample.sample_id),
            provider=provider.provider_name,
            product=provider.product_name,
            adapter_version=provider.adapter_version,
            timestamp=now or datetime.now(UTC),
            benchmark_sample_id=sample.sample_id,
            request_mode=RequestMode.KNOWN_TARGET,
            request_configuration={"locale": request.locale, "target_text": request.target_text},
            response_latency_seconds=time.perf_counter() - started,
            audio_duration_seconds=request.audio.duration_seconds,
            normalized_result=result,
            raw_response=cast(JsonValue, raw),
            status=RunStatus.SUCCEEDED,
        )
    except Exception as exc:
        retryable = isinstance(exc, ProviderAdapterError) and exc.retryable
        code = exc.code if isinstance(exc, ProviderAdapterError) else None
        run = ProviderRun(
            run_id=_run_id(provider.provider_name, sample.sample_id),
            provider=provider.provider_name,
            product=provider.product_name,
            adapter_version=provider.adapter_version,
            timestamp=now or datetime.now(UTC),
            benchmark_sample_id=sample.sample_id,
            request_mode=RequestMode.KNOWN_TARGET,
            request_configuration={"locale": request.locale, "target_text": request.target_text},
            response_latency_seconds=time.perf_counter() - started,
            audio_duration_seconds=request.audio.duration_seconds,
            raw_response=cast(JsonValue, raw),
            status=RunStatus.FAILED,
            error=ProviderError(
                error_type=type(exc).__name__,
                message=str(exc),
                retryable=retryable,
                provider_code=code,
            ),
        )
    if output_dir is not None:
        write_model(output_dir / f"{run.run_id}.json", run)
    return run

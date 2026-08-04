"""Import sanitized production captures without converting fixtures into live evidence."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from benchmark.audio import sha256_file
from benchmark.models import (
    BenchmarkSample,
    EvidenceOrigin,
    KnownTargetAssessmentResult,
    PhoneAssessment,
    ProviderRun,
    RequestMode,
    RunStatus,
    SyllableAssessment,
    TimeSpan,
)
from benchmark.storage import write_model


def _number(value: object) -> float | None:
    if isinstance(value, int | float):
        return max(0.0, min(100.0, float(value)))
    return None


def _nonnegative(value: object) -> float | None:
    if isinstance(value, int | float) and value >= 0:
        return float(value)
    return None


def _span(value: object) -> TimeSpan | None:
    if not isinstance(value, dict):
        return None
    start = value.get("start_seconds")
    end = value.get("end_seconds")
    if not isinstance(start, int | float) or not isinstance(end, int | float) or end < start:
        return None
    return TimeSpan(start_seconds=float(start), end_seconds=float(end))


def _classification(value: object) -> str | None:
    if isinstance(value, str) and value:
        return value
    if isinstance(value, list):
        labels = [str(item) for item in value if item]
        return ";".join(labels) or None
    return None


def _tone(value: object) -> str | None:
    if isinstance(value, int | float) and int(value) in {0, 1, 2, 3, 4}:
        return f"T{int(value)}"
    if isinstance(value, str) and value:
        return value
    return None


def normalized_result(evidence: dict[str, Any]) -> KnownTargetAssessmentResult:
    syllables: list[SyllableAssessment] = []
    raw_syllables = evidence.get("syllables")
    if not isinstance(raw_syllables, list):
        raw_syllables = []
    for raw_syllable in raw_syllables:
        if not isinstance(raw_syllable, dict):
            continue
        phones: list[PhoneAssessment] = []
        raw_phones = raw_syllable.get("phones")
        if not isinstance(raw_phones, list):
            raw_phones = []
        for raw_phone in raw_phones:
            if not isinstance(raw_phone, dict):
                continue
            phone = raw_phone.get("phone")
            phones.append(
                PhoneAssessment(
                    phone=str(phone) if phone is not None else "unknown",
                    score=_number(raw_phone.get("pronunciation_score", raw_phone.get("score"))),
                    span=_span(raw_phone.get("timing", raw_phone.get("span"))),
                    error_classification=_classification(
                        raw_phone.get(
                            "error_classifications", raw_phone.get("error_classification")
                        )
                    ),
                )
            )
        classifications = raw_syllable.get("error_classifications")
        syllables.append(
            SyllableAssessment(
                text=(
                    str(raw_syllable["text"])
                    if raw_syllable.get("text") is not None
                    else None
                ),
                pinyin=(
                    str(raw_syllable["pinyin"])
                    if raw_syllable.get("pinyin") is not None
                    else None
                ),
                score=_number(
                    raw_syllable.get("pronunciation_score", raw_syllable.get("score"))
                ),
                phones=tuple(phones),
                reference_tone=_tone(raw_syllable.get("reference_tone")),
                detected_tone=_tone(raw_syllable.get("detected_tone")),
                tone_score=_number(raw_syllable.get("tone_score")),
                span=_span(raw_syllable.get("timing", raw_syllable.get("span"))),
                error_classifications=(
                    tuple(str(item) for item in classifications)
                    if isinstance(classifications, list)
                    else ()
                ),
            )
        )
    unsupported = evidence.get("unsupported_capabilities")
    provider_errors = evidence.get("provider_error_classifications")
    return KnownTargetAssessmentResult(
        overall_score=_number(evidence.get("overall_score")),
        pronunciation_score=_number(evidence.get("pronunciation_score")),
        fluency_score=_number(evidence.get("fluency_score")),
        completeness_score=_number(evidence.get("completeness_score")),
        syllables=tuple(syllables),
        provider_error_classifications=(
            tuple(str(item) for item in provider_errors)
            if isinstance(provider_errors, list)
            else ()
        ),
        unsupported_capabilities=(
            tuple(str(item) for item in unsupported) if isinstance(unsupported, list) else ()
        ),
    )


def import_live_capture(
    capture_path: Path,
    sample: BenchmarkSample,
    *,
    output_dir: Path,
) -> ProviderRun:
    """Validate audio/target identity and persist a benchmark ProviderRun."""
    payload = json.loads(capture_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("capture must be a JSON object")
    if payload.get("capture_type") != EvidenceOrigin.LIVE_CAPTURED_SANITIZED.value.upper():
        raise ValueError("only LIVE_CAPTURED_SANITIZED captures can be imported as live evidence")
    if sample.audio is None or not sample.intended_text:
        raise ValueError("capture import requires a recorded known-target sample")
    audio_hash = sample.audio.sha256 or sha256_file(sample.audio.asset_path)
    if payload.get("audio_sha256") != audio_hash:
        raise ValueError("capture audio hash does not match the benchmark sample")
    if payload.get("target") != sample.intended_text:
        raise ValueError("capture target does not match the benchmark sample")
    evidence = payload.get("normalized_evidence")
    if not isinstance(evidence, dict):
        raise ValueError("capture has no normalized evidence object")
    provider = str(payload.get("provider") or "undocumented")
    product = str(payload.get("product") or "undocumented")
    timings_ms = payload.get("transport_timings_ms")
    timings = (
        {
            str(key): float(value) / 1000
            for key, value in timings_ms.items()
            if isinstance(value, int | float)
        }
        if isinstance(timings_ms, dict)
        else {}
    )
    configuration = payload.get("request_configuration")
    timestamp_value = payload.get("timestamp")
    timestamp = (
        datetime.fromisoformat(timestamp_value.replace("Z", "+00:00"))
        if isinstance(timestamp_value, str)
        else datetime.now(UTC)
    )
    run = ProviderRun(
        run_id=f"{provider}-{sample.sample_id}-{uuid.uuid4().hex[:12]}",
        provider=provider,
        product=product,
        provider_version=str(payload.get("provider_version") or "undocumented"),
        adapter_version=str(payload.get("adapter_version") or "undocumented"),
        git_commit_sha=str(payload.get("git_commit_sha") or "undocumented"),
        timestamp=timestamp,
        benchmark_sample_id=sample.sample_id,
        request_mode=RequestMode.KNOWN_TARGET,
        request_configuration=configuration if isinstance(configuration, dict) else {},
        audio_sha256=audio_hash,
        sample_rate_hz=sample.audio.sample_rate_hz,
        transport_timings_seconds=timings,
        response_latency_seconds=timings.get("total"),
        audio_duration_seconds=sample.audio.duration_seconds,
        estimated_billable_units=_nonnegative(payload.get("estimated_billable_units")),
        estimated_cost_usd=_nonnegative(payload.get("estimated_cost_usd")),
        normalized_result=normalized_result(evidence),
        raw_response=payload.get("raw_response"),
        raw_response_sha256=(
            str(payload["raw_response_sha256"])
            if payload.get("raw_response_sha256")
            else None
        ),
        evidence_origin=EvidenceOrigin.LIVE_CAPTURED_SANITIZED,
        status=RunStatus.SUCCEEDED,
    )
    write_model(output_dir / f"{run.run_id}.json", run)
    return run

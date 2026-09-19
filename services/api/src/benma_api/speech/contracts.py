"""Separate unknown-target and known-target production provider ports."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class UnknownTargetPerceptionInput:
    """Audio-only evidence input. Semantic target/context cannot be represented."""

    utterance_id: uuid.UUID
    canonical_audio: bytes
    mime_type: str
    language_hint: str
    timeout_seconds: float


@dataclass(frozen=True, slots=True)
class PerceptionEvidence:
    transcript: str
    alternatives: list[dict[str, Any]] | None
    tokens: list[dict[str, Any]] | None
    segments: list[dict[str, Any]] | None
    provider_uncertainty: Any | None
    detected_language: str | None
    evidence_status: str
    detected_languages: list[dict[str, Any]] | None = None

    def normalized(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "transcript": self.transcript,
            "evidence_status": self.evidence_status,
        }
        for key in (
            "alternatives",
            "tokens",
            "segments",
            "provider_uncertainty",
            "detected_language",
            "detected_languages",
        ):
            value = getattr(self, key)
            if value is not None:
                result[key] = value
        return result


@dataclass(frozen=True, slots=True)
class PerceptionProviderResponse:
    evidence: PerceptionEvidence
    raw_payload: object
    provider_version: str | None = None


class PerceptionPort(Protocol):
    provider_name: str
    product_name: str
    adapter_version: str

    def perceive(self, request: UnknownTargetPerceptionInput) -> PerceptionProviderResponse: ...


@dataclass(frozen=True, slots=True)
class KnownTargetAssessmentInput:
    attempt_id: uuid.UUID
    canonical_audio: bytes
    mime_type: str
    target_snapshot: dict[str, Any]
    timeout_seconds: float


@dataclass(frozen=True, slots=True)
class AssessmentEvidence:
    overall_score: float | None = None
    pronunciation_score: float | None = None
    fluency_score: float | None = None
    completeness_score: float | None = None
    phone_score: float | None = None
    tone_score: float | None = None
    integrity_score: float | None = None
    syllables: list[dict[str, Any]] | None = None
    audio_quality: dict[str, Any] | None = None
    provider_error_classifications: list[str] | None = None
    unsupported_capabilities: list[str] | None = None
    evidence_status: str = "live_provider"

    def normalized(self) -> dict[str, Any]:
        result: dict[str, Any] = {"evidence_status": self.evidence_status}
        for key in (
            "overall_score",
            "pronunciation_score",
            "fluency_score",
            "completeness_score",
            "phone_score",
            "tone_score",
            "integrity_score",
            "syllables",
            "audio_quality",
            "provider_error_classifications",
            "unsupported_capabilities",
        ):
            value = getattr(self, key)
            if value is not None:
                result[key] = value
        return result


@dataclass(frozen=True, slots=True)
class AssessmentProviderResponse:
    evidence: AssessmentEvidence
    raw_payload: object
    provider_version: str | None = None
    request_configuration: dict[str, Any] | None = None
    transport_timings_ms: dict[str, int] | None = None


class PronunciationAssessmentPort(Protocol):
    provider_name: str
    product_name: str
    adapter_version: str

    def assess(self, request: KnownTargetAssessmentInput) -> AssessmentProviderResponse: ...

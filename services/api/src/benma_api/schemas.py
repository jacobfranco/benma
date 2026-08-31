"""Public API schemas with strict write contracts."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class DevAuthRequest(StrictRequest):
    phone_number: str = Field(min_length=7, max_length=32)


class AuthTokenResponse(BaseModel):
    token: str
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime
    account_id: uuid.UUID


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime


class PracticeSessionCreate(StrictRequest):
    mode: Literal["perception_test", "pronunciation"]
    metadata: dict[str, Any] = Field(default_factory=dict)


class PracticeSessionResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    mode: str
    started_at: datetime
    ended_at: datetime | None
    metadata: dict[str, Any]


class AudioAssetResponse(BaseModel):
    id: uuid.UUID
    kind: str
    mime_type: str
    sha256: str
    size_bytes: int
    sample_rate_hz: int | None
    channels: int | None
    sample_width_bits: int | None
    duration_seconds: float | None


class UtteranceResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    practice_session_id: uuid.UUID | None
    created_at: datetime
    original_audio: AudioAssetResponse
    canonical_audio: AudioAssetResponse
    audio_url: str


class UnknownPerceptionRequest(StrictRequest):
    language_hint: Literal["zh"] = "zh"
    timeout_seconds: float = Field(default=30.0, ge=1, le=120)


class PerceptionRunResponse(BaseModel):
    id: uuid.UUID
    utterance_id: uuid.UUID
    provider: str
    product: str
    provider_version: str | None
    adapter_version: str
    transcript: str | None
    alternatives: list[dict[str, Any]] | None
    provider_uncertainty: Any | None
    normalized_result: dict[str, Any] | None
    latency_ms: int | None
    created_at: datetime
    status: str
    error_code: str | None
    error_message: str | None


class ContextualInterpretationUncertainty(StrictRequest):
    level: Literal["unknown", "low", "medium", "high"] = "unknown"
    rationale: str | None = Field(default=None, max_length=1000)
    alternatives: list[str] = Field(default_factory=list, max_length=10)


class ContextualInterpretationCreate(StrictRequest):
    context_snapshot: dict[str, Any] = Field(default_factory=dict)


class ContextualInterpretationRunResponse(BaseModel):
    id: uuid.UUID
    perception_run_id: uuid.UUID
    interpreter: str
    interpreter_version: str
    interpreter_configuration: dict[str, Any]
    context_snapshot: dict[str, Any]
    decision: Literal["preserve", "infer", "clarify"]
    inferred_text: str | None
    uncertainty: ContextualInterpretationUncertainty
    clarification_needed: bool
    created_at: datetime


class UserCorrectionCreate(StrictRequest):
    intended_text: str = Field(min_length=1, max_length=500)
    perception_run_id: uuid.UUID | None = None


class UserCorrectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    utterance_id: uuid.UUID
    perception_run_id: uuid.UUID | None
    intended_text: str
    created_at: datetime


class PronunciationTargetCreate(StrictRequest):
    text: str = Field(min_length=1, max_length=200)
    target_source: Literal["generated", "manual", "imported"] = "manual"


class PronunciationTargetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    text: str
    display_pinyin: str
    pinyin_syllables: list[str]
    lexical_tones: list[int | None]
    target_source: str
    pinyin_source: str
    pinyin_alternatives: list[list[str]]
    syllable_units: list[dict[str, Any]]
    surface_tone_expectation: dict[str, Any]
    parent_target_id: uuid.UUID | None
    created_at: datetime


class PinyinCorrectionCreate(StrictRequest):
    pinyin: str = Field(min_length=2, max_length=500)


class PronunciationAttemptCreate(StrictRequest):
    utterance_id: uuid.UUID
    target_id: uuid.UUID


class PronunciationAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    utterance_id: uuid.UUID
    target_id: uuid.UUID
    created_at: datetime


class AssessmentRequest(StrictRequest):
    timeout_seconds: float = Field(default=30.0, ge=1, le=120)


class AssessmentRunResponse(BaseModel):
    id: uuid.UUID
    pronunciation_attempt_id: uuid.UUID
    provider: str
    product: str
    provider_version: str | None
    adapter_version: str
    target_snapshot: dict[str, Any]
    git_commit_sha: str
    audio_sha256: str | None
    sample_rate_hz: int | None
    request_configuration: dict[str, Any]
    transport_timings_ms: dict[str, int]
    estimated_billable_units: float | None
    estimated_cost_usd: float | None
    normalized_result: dict[str, Any] | None
    latency_ms: int | None
    created_at: datetime
    status: str
    error_code: str | None
    error_message: str | None


class ReferenceSpeechRequestBody(StrictRequest):
    force: bool = False
    timeout_seconds: float = Field(default=30.0, ge=1, le=120)


class ReferenceSpeechResponse(BaseModel):
    id: uuid.UUID
    target_id: uuid.UUID
    provider: str
    voice: str
    locale: str
    model_version: str
    generation_config: dict[str, Any]
    target_snapshot: dict[str, Any]
    status: str
    error_code: str | None
    error_message: str | None
    audio_url: str | None
    acoustic_result: dict[str, Any] | None
    created_at: datetime


class AcousticRunResponse(BaseModel):
    id: uuid.UUID
    utterance_id: uuid.UUID
    algorithm: str
    algorithm_version: str
    parameters: dict[str, Any]
    normalized_result: dict[str, Any] | None
    latency_ms: int | None
    status: str
    error_code: str | None
    error_message: str | None
    created_at: datetime


class AlignmentRunResponse(BaseModel):
    id: uuid.UUID
    pronunciation_attempt_id: uuid.UUID
    algorithm: str
    algorithm_version: str
    normalized_result: dict[str, Any] | None
    quality: str
    latency_ms: int | None
    status: str
    error_code: str | None
    error_message: str | None
    created_at: datetime


class InterpretationRunResponse(BaseModel):
    id: uuid.UUID
    pronunciation_attempt_id: uuid.UUID
    interpreter_version: str
    interpreter_configuration: dict[str, Any]
    input_evidence_run_ids: dict[str, str | None]
    structured_observations: list[dict[str, Any]]
    capability_state: str
    created_at: datetime


class PronunciationAnalyzeRequest(StrictRequest):
    reuse_existing: bool = True
    rerun_provider: bool = False
    rerun_acoustics: bool = False
    rerun_alignment: bool = False


class PronunciationSyllableResult(BaseModel):
    syllable_index: int
    characters: str
    pinyin: str
    lexical_tone: int | None
    expected_surface_tone: int | None
    surface_tone_reason: list[dict[str, Any]]
    provider_evidence: dict[str, Any] | None
    acoustic_evidence: dict[str, Any] | None
    timing: dict[str, Any] | None
    interpretation: dict[str, Any] | None
    capability_state: str


class PronunciationResultResponse(BaseModel):
    attempt: PronunciationAttemptResponse
    target: PronunciationTargetResponse
    recording_audio_url: str
    reference_audio: ReferenceSpeechResponse | None
    overall_evidence: dict[str, Any]
    syllables: list[PronunciationSyllableResult]
    assessment: AssessmentRunResponse | None
    acoustic: AcousticRunResponse | None
    alignment: AlignmentRunResponse | None
    interpretation: InterpretationRunResponse | None
    capability_policy: dict[str, Any]


class AttemptComparisonRequest(StrictRequest):
    first_attempt_id: uuid.UUID
    second_attempt_id: uuid.UUID


class AttemptComparisonResponse(BaseModel):
    first: PronunciationResultResponse
    second: PronunciationResultResponse
    disclaimer: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    retryable: bool
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail

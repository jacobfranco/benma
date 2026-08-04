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
    created_at: datetime


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
    normalized_result: dict[str, Any] | None
    latency_ms: int | None
    created_at: datetime
    status: str
    error_code: str | None
    error_message: str | None


class ErrorDetail(BaseModel):
    code: str
    message: str
    retryable: bool
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail

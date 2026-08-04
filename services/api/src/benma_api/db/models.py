"""Production persistence models; deliberately independent of benchmark models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from benma_api.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


def utcnow() -> datetime:
    return datetime.now(UTC)


class Account(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "accounts"
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)


class AuthIdentity(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "auth_identities"
    __table_args__ = (
        UniqueConstraint("method", "phone_e164", name="uq_auth_identity_method_phone"),
        UniqueConstraint("method", "provider_subject", name="uq_auth_identity_method_subject"),
    )
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), index=True)
    method: Mapped[str] = mapped_column(String(32), nullable=False)
    phone_e164: Mapped[str | None] = mapped_column(String(32))
    provider_subject: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuthSession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "auth_sessions"
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PracticeSession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "practice_sessions"
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), index=True)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    session_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)


class AudioAsset(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audio_assets"
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), index=True)
    storage_key: Mapped[str] = mapped_column(String(512), unique=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(127), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sample_rate_hz: Mapped[int | None] = mapped_column(Integer)
    channels: Mapped[int | None] = mapped_column(Integer)
    sample_width_bits: Mapped[int | None] = mapped_column(Integer)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    source_asset_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("audio_assets.id"))


class Utterance(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "utterances"
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), index=True)
    practice_session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("practice_sessions.id"), index=True
    )
    original_audio_asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("audio_assets.id"))
    canonical_audio_asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("audio_assets.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    original_audio: Mapped[AudioAsset] = relationship(foreign_keys=[original_audio_asset_id])
    canonical_audio: Mapped[AudioAsset] = relationship(foreign_keys=[canonical_audio_asset_id])


class PronunciationTarget(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "pronunciation_targets"
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    display_pinyin: Mapped[str] = mapped_column(Text, nullable=False)
    pinyin_syllables: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    lexical_tones: Mapped[list[int | None]] = mapped_column(JSON, nullable=False)
    target_source: Mapped[str] = mapped_column(String(32), nullable=False)
    pinyin_source: Mapped[str] = mapped_column(String(64), nullable=False)
    pinyin_alternatives: Mapped[list[list[str]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PronunciationAttempt(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "pronunciation_attempts"
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), index=True)
    utterance_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utterances.id"), index=True)
    target_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pronunciation_targets.id"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EvidenceMixin:
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    product: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_version: Mapped[str | None] = mapped_column(String(64))
    adapter_version: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_result: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    raw_payload_json: Mapped[Any | None] = mapped_column(JSON)
    raw_payload_text: Mapped[str | None] = mapped_column(Text)
    raw_payload_sha256: Mapped[str | None] = mapped_column(String(64))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)


class PerceptionRun(UUIDPrimaryKeyMixin, EvidenceMixin, Base):
    __tablename__ = "perception_runs"
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), index=True)
    utterance_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utterances.id"), index=True)
    transcript: Mapped[str | None] = mapped_column(Text)
    alternatives: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    provider_uncertainty: Mapped[Any | None] = mapped_column(JSON)


class AssessmentRun(UUIDPrimaryKeyMixin, EvidenceMixin, Base):
    __tablename__ = "assessment_runs"
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), index=True)
    pronunciation_attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pronunciation_attempts.id"), index=True
    )
    target_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


class AcousticRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "acoustic_runs"
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), index=True)
    utterance_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utterances.id"), index=True)
    algorithm: Mapped[str] = mapped_column(String(128), nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_result: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    status: Mapped[str] = mapped_column(String(32), nullable=False)


class UserCorrection(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "user_corrections"
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), index=True)
    utterance_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utterances.id"), index=True)
    perception_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("perception_runs.id"))
    intended_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


APPEND_ONLY_MODELS = (PerceptionRun, AssessmentRun, AcousticRun, UserCorrection)

"""Production speech foundation schema.

Revision ID: 0001
Revises: None
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def id_column() -> sa.Column[object]:
    return sa.Column("id", sa.Uuid(), nullable=False)


def created_column() -> sa.Column[object]:
    return sa.Column("created_at", sa.DateTime(timezone=True), nullable=False)


def evidence_columns() -> tuple[sa.Column[object], ...]:
    return (
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("product", sa.String(length=128), nullable=False),
        sa.Column("provider_version", sa.String(length=64), nullable=True),
        sa.Column("adapter_version", sa.String(length=64), nullable=False),
        sa.Column("normalized_result", sa.JSON(), nullable=True),
        sa.Column("raw_payload_json", sa.JSON(), nullable=True),
        sa.Column("raw_payload_text", sa.Text(), nullable=True),
        sa.Column("raw_payload_sha256", sa.String(length=64), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        created_column(),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )


def account_fk() -> sa.Column[object]:
    return sa.Column(
        "account_id", sa.Uuid(), sa.ForeignKey("accounts.id"), nullable=False
    )


def upgrade() -> None:
    op.create_table(
        "accounts",
        id_column(),
        created_column(),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_accounts")),
    )
    op.create_table(
        "auth_identities",
        id_column(),
        account_fk(),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column("phone_e164", sa.String(length=32), nullable=True),
        sa.Column("provider_subject", sa.String(length=255), nullable=True),
        created_column(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_identities")),
        sa.UniqueConstraint("method", "phone_e164", name="uq_auth_identity_method_phone"),
        sa.UniqueConstraint(
            "method", "provider_subject", name="uq_auth_identity_method_subject"
        ),
    )
    op.create_index(op.f("ix_auth_identities_account_id"), "auth_identities", ["account_id"])
    op.create_table(
        "auth_sessions",
        id_column(),
        account_fk(),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        created_column(),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_sessions")),
    )
    op.create_index(op.f("ix_auth_sessions_account_id"), "auth_sessions", ["account_id"])
    op.create_index(op.f("ix_auth_sessions_expires_at"), "auth_sessions", ["expires_at"])
    op.create_index(
        op.f("ix_auth_sessions_token_hash"), "auth_sessions", ["token_hash"], unique=True
    )
    op.create_table(
        "practice_sessions",
        id_column(),
        account_fk(),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_practice_sessions")),
    )
    op.create_index(
        op.f("ix_practice_sessions_account_id"), "practice_sessions", ["account_id"]
    )
    op.create_table(
        "audio_assets",
        id_column(),
        account_fk(),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("mime_type", sa.String(length=127), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sample_rate_hz", sa.Integer(), nullable=True),
        sa.Column("channels", sa.Integer(), nullable=True),
        sa.Column("sample_width_bits", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        created_column(),
        sa.Column("source_asset_id", sa.Uuid(), sa.ForeignKey("audio_assets.id"), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audio_assets")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_audio_assets_storage_key")),
    )
    op.create_index(op.f("ix_audio_assets_account_id"), "audio_assets", ["account_id"])
    op.create_table(
        "utterances",
        id_column(),
        account_fk(),
        sa.Column(
            "practice_session_id",
            sa.Uuid(),
            sa.ForeignKey("practice_sessions.id"),
            nullable=True,
        ),
        sa.Column(
            "original_audio_asset_id",
            sa.Uuid(),
            sa.ForeignKey("audio_assets.id"),
            nullable=False,
        ),
        sa.Column(
            "canonical_audio_asset_id",
            sa.Uuid(),
            sa.ForeignKey("audio_assets.id"),
            nullable=False,
        ),
        created_column(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_utterances")),
    )
    op.create_index(op.f("ix_utterances_account_id"), "utterances", ["account_id"])
    op.create_index(
        op.f("ix_utterances_practice_session_id"), "utterances", ["practice_session_id"]
    )
    op.create_table(
        "pronunciation_targets",
        id_column(),
        account_fk(),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("display_pinyin", sa.Text(), nullable=False),
        sa.Column("pinyin_syllables", sa.JSON(), nullable=False),
        sa.Column("lexical_tones", sa.JSON(), nullable=False),
        sa.Column("target_source", sa.String(length=32), nullable=False),
        sa.Column("pinyin_source", sa.String(length=64), nullable=False),
        sa.Column("pinyin_alternatives", sa.JSON(), nullable=False),
        created_column(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pronunciation_targets")),
    )
    op.create_index(
        op.f("ix_pronunciation_targets_account_id"),
        "pronunciation_targets",
        ["account_id"],
    )
    op.create_table(
        "pronunciation_attempts",
        id_column(),
        account_fk(),
        sa.Column("utterance_id", sa.Uuid(), sa.ForeignKey("utterances.id"), nullable=False),
        sa.Column(
            "target_id", sa.Uuid(), sa.ForeignKey("pronunciation_targets.id"), nullable=False
        ),
        created_column(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pronunciation_attempts")),
    )
    op.create_index(
        op.f("ix_pronunciation_attempts_account_id"),
        "pronunciation_attempts",
        ["account_id"],
    )
    op.create_index(
        op.f("ix_pronunciation_attempts_target_id"),
        "pronunciation_attempts",
        ["target_id"],
    )
    op.create_index(
        op.f("ix_pronunciation_attempts_utterance_id"),
        "pronunciation_attempts",
        ["utterance_id"],
    )
    op.create_table(
        "perception_runs",
        id_column(),
        account_fk(),
        sa.Column("utterance_id", sa.Uuid(), sa.ForeignKey("utterances.id"), nullable=False),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("alternatives", sa.JSON(), nullable=True),
        sa.Column("provider_uncertainty", sa.JSON(), nullable=True),
        *evidence_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_perception_runs")),
    )
    op.create_index(
        op.f("ix_perception_runs_account_id"), "perception_runs", ["account_id"]
    )
    op.create_index(
        op.f("ix_perception_runs_utterance_id"), "perception_runs", ["utterance_id"]
    )
    op.create_table(
        "assessment_runs",
        id_column(),
        account_fk(),
        sa.Column(
            "pronunciation_attempt_id",
            sa.Uuid(),
            sa.ForeignKey("pronunciation_attempts.id"),
            nullable=False,
        ),
        sa.Column("target_snapshot", sa.JSON(), nullable=False),
        *evidence_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assessment_runs")),
    )
    op.create_index(
        op.f("ix_assessment_runs_account_id"), "assessment_runs", ["account_id"]
    )
    op.create_index(
        op.f("ix_assessment_runs_pronunciation_attempt_id"),
        "assessment_runs",
        ["pronunciation_attempt_id"],
    )
    op.create_table(
        "acoustic_runs",
        id_column(),
        account_fk(),
        sa.Column("utterance_id", sa.Uuid(), sa.ForeignKey("utterances.id"), nullable=False),
        sa.Column("algorithm", sa.String(length=128), nullable=False),
        sa.Column("algorithm_version", sa.String(length=64), nullable=False),
        sa.Column("normalized_result", sa.JSON(), nullable=True),
        created_column(),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_acoustic_runs")),
    )
    op.create_index(op.f("ix_acoustic_runs_account_id"), "acoustic_runs", ["account_id"])
    op.create_index(
        op.f("ix_acoustic_runs_utterance_id"), "acoustic_runs", ["utterance_id"]
    )
    op.create_table(
        "user_corrections",
        id_column(),
        account_fk(),
        sa.Column("utterance_id", sa.Uuid(), sa.ForeignKey("utterances.id"), nullable=False),
        sa.Column(
            "perception_run_id",
            sa.Uuid(),
            sa.ForeignKey("perception_runs.id"),
            nullable=True,
        ),
        sa.Column("intended_text", sa.Text(), nullable=False),
        created_column(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_corrections")),
    )
    op.create_index(
        op.f("ix_user_corrections_account_id"), "user_corrections", ["account_id"]
    )
    op.create_index(
        op.f("ix_user_corrections_utterance_id"), "user_corrections", ["utterance_id"]
    )


def downgrade() -> None:
    for table in (
        "user_corrections",
        "acoustic_runs",
        "assessment_runs",
        "perception_runs",
        "pronunciation_attempts",
        "pronunciation_targets",
        "utterances",
        "audio_assets",
        "practice_sessions",
        "auth_sessions",
        "auth_identities",
        "accounts",
    ):
        op.drop_table(table)

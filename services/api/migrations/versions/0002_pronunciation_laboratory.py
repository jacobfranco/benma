"""Pronunciation laboratory evidence and reference assets.

Revision ID: 0002
Revises: 0001
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def id_column() -> sa.Column[object]:
    return sa.Column("id", sa.Uuid(), nullable=False)


def account_fk() -> sa.Column[object]:
    return sa.Column("account_id", sa.Uuid(), sa.ForeignKey("accounts.id"), nullable=False)


def created_column() -> sa.Column[object]:
    return sa.Column("created_at", sa.DateTime(timezone=True), nullable=False)


def upgrade() -> None:
    with op.batch_alter_table("pronunciation_targets") as batch:
        batch.add_column(
            sa.Column("syllable_units", sa.JSON(), nullable=False, server_default="[]")
        )
        batch.add_column(
            sa.Column("surface_tone_expectation", sa.JSON(), nullable=False, server_default="{}")
        )
        batch.add_column(sa.Column("parent_target_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_pronunciation_targets_parent_target_id_pronunciation_targets",
            "pronunciation_targets",
            ["parent_target_id"],
            ["id"],
        )
        batch.create_index(
            "ix_pronunciation_targets_parent_target_id", ["parent_target_id"], unique=False
        )

    with op.batch_alter_table("acoustic_runs") as batch:
        batch.add_column(sa.Column("parameters", sa.JSON(), nullable=False, server_default="{}"))
        batch.add_column(sa.Column("latency_ms", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("error_code", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("error_message", sa.Text(), nullable=True))

    op.create_table(
        "reference_speech_assets",
        id_column(),
        account_fk(),
        sa.Column(
            "target_id",
            sa.Uuid(),
            sa.ForeignKey("pronunciation_targets.id"),
            nullable=False,
        ),
        sa.Column("audio_asset_id", sa.Uuid(), sa.ForeignKey("audio_assets.id"), nullable=True),
        sa.Column("cache_key", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("voice", sa.String(length=160), nullable=False),
        sa.Column("locale", sa.String(length=32), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("generation_config", sa.JSON(), nullable=False),
        sa.Column("target_snapshot", sa.JSON(), nullable=False),
        sa.Column("acoustic_result", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        created_column(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reference_speech_assets")),
    )
    op.create_index(
        op.f("ix_reference_speech_assets_account_id"),
        "reference_speech_assets",
        ["account_id"],
    )
    op.create_index(
        op.f("ix_reference_speech_assets_target_id"),
        "reference_speech_assets",
        ["target_id"],
    )
    op.create_index(
        "ix_reference_speech_assets_account_cache",
        "reference_speech_assets",
        ["account_id", "cache_key"],
    )

    op.create_table(
        "alignment_runs",
        id_column(),
        account_fk(),
        sa.Column("utterance_id", sa.Uuid(), sa.ForeignKey("utterances.id"), nullable=False),
        sa.Column(
            "pronunciation_attempt_id",
            sa.Uuid(),
            sa.ForeignKey("pronunciation_attempts.id"),
            nullable=False,
        ),
        sa.Column("target_snapshot", sa.JSON(), nullable=False),
        sa.Column("algorithm", sa.String(length=128), nullable=False),
        sa.Column("algorithm_version", sa.String(length=64), nullable=False),
        sa.Column("normalized_result", sa.JSON(), nullable=True),
        sa.Column("raw_result", sa.JSON(), nullable=True),
        sa.Column("quality", sa.String(length=32), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        created_column(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alignment_runs")),
    )
    for column in ("account_id", "utterance_id", "pronunciation_attempt_id"):
        op.create_index(op.f(f"ix_alignment_runs_{column}"), "alignment_runs", [column])

    op.create_table(
        "pronunciation_interpretation_runs",
        id_column(),
        account_fk(),
        sa.Column(
            "pronunciation_attempt_id",
            sa.Uuid(),
            sa.ForeignKey("pronunciation_attempts.id"),
            nullable=False,
        ),
        sa.Column("interpreter_version", sa.String(length=64), nullable=False),
        sa.Column("input_evidence_run_ids", sa.JSON(), nullable=False),
        sa.Column("structured_observations", sa.JSON(), nullable=False),
        sa.Column("capability_state", sa.String(length=32), nullable=False),
        created_column(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pronunciation_interpretation_runs")),
    )
    op.create_index(
        op.f("ix_pronunciation_interpretation_runs_account_id"),
        "pronunciation_interpretation_runs",
        ["account_id"],
    )
    op.create_index(
        op.f("ix_pronunciation_interpretation_runs_pronunciation_attempt_id"),
        "pronunciation_interpretation_runs",
        ["pronunciation_attempt_id"],
    )

    op.create_table(
        "research_exports",
        id_column(),
        account_fk(),
        sa.Column(
            "pronunciation_attempt_id",
            sa.Uuid(),
            sa.ForeignKey("pronunciation_attempts.id"),
            nullable=False,
        ),
        sa.Column("export_metadata", sa.JSON(), nullable=False),
        created_column(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_research_exports")),
    )
    op.create_index(
        op.f("ix_research_exports_account_id"), "research_exports", ["account_id"]
    )
    op.create_index(
        op.f("ix_research_exports_pronunciation_attempt_id"),
        "research_exports",
        ["pronunciation_attempt_id"],
    )


def downgrade() -> None:
    for table in (
        "research_exports",
        "pronunciation_interpretation_runs",
        "alignment_runs",
        "reference_speech_assets",
    ):
        op.drop_table(table)
    with op.batch_alter_table("acoustic_runs") as batch:
        for column in ("error_message", "error_code", "latency_ms", "parameters"):
            batch.drop_column(column)
    with op.batch_alter_table("pronunciation_targets") as batch:
        batch.drop_index("ix_pronunciation_targets_parent_target_id")
        batch.drop_constraint(
            "fk_pronunciation_targets_parent_target_id_pronunciation_targets", type_="foreignkey"
        )
        for column in ("parent_target_id", "surface_tone_expectation", "syllable_units"):
            batch.drop_column(column)

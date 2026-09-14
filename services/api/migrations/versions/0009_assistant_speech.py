"""Add append-only assistant speech provenance.

Revision ID: 0009
Revises: 0008
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assistant_speech_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("assistant_generation_run_id", sa.Uuid(), nullable=False),
        sa.Column("assistant_turn_id", sa.Uuid(), nullable=False),
        sa.Column("audio_asset_id", sa.Uuid(), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("product", sa.String(length=128), nullable=False),
        sa.Column("provider_version", sa.String(length=64), nullable=True),
        sa.Column("adapter_version", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("voice", sa.String(length=160), nullable=False),
        sa.Column("locale", sa.String(length=32), nullable=False),
        sa.Column("generation_configuration", sa.JSON(), nullable=False),
        sa.Column("text_snapshot", sa.Text(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('succeeded', 'failed') AND "
            "length(trim(text_snapshot)) > 0 AND "
            "((status = 'succeeded' AND audio_asset_id IS NOT NULL AND "
            "error_code IS NULL AND error_message IS NULL) OR "
            "(status = 'failed' AND audio_asset_id IS NULL AND error_code IS NOT NULL))",
            name="ck_assistant_speech_result",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id", "account_id"],
            ["conversations.id", "conversations.account_id"],
            name="fk_assistant_speech_runs_conversation_account",
        ),
        sa.ForeignKeyConstraint(
            ["assistant_generation_run_id"],
            ["assistant_generation_runs.id"],
            name="fk_assistant_speech_runs_generation",
        ),
        sa.ForeignKeyConstraint(
            ["assistant_turn_id"],
            ["conversation_turns.id"],
            name="fk_assistant_speech_runs_turn",
        ),
        sa.ForeignKeyConstraint(
            ["audio_asset_id"],
            ["audio_assets.id"],
            name="fk_assistant_speech_runs_audio",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assistant_speech_runs")),
    )
    for column in (
        "account_id",
        "conversation_id",
        "assistant_generation_run_id",
        "assistant_turn_id",
        "audio_asset_id",
    ):
        op.create_index(
            op.f(f"ix_assistant_speech_runs_{column}"),
            "assistant_speech_runs",
            [column],
        )


def downgrade() -> None:
    op.drop_table("assistant_speech_runs")

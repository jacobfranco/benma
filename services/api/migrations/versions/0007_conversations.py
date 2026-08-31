"""Add persisted Free Talk conversations and turns.

Revision ID: 0007
Revises: 0006
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "account_id",
            sa.Uuid(),
            sa.ForeignKey("accounts.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversations")),
        sa.UniqueConstraint(
            "id",
            "account_id",
            name="uq_conversations_id_account_id",
        ),
    )
    op.create_index(
        op.f("ix_conversations_account_id"),
        "conversations",
        ["account_id"],
    )

    op.create_table(
        "conversation_turns",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("assistant_text", sa.Text(), nullable=True),
        sa.Column(
            "utterance_id",
            sa.Uuid(),
            sa.ForeignKey("utterances.id"),
            nullable=True,
        ),
        sa.Column(
            "perception_run_id",
            sa.Uuid(),
            sa.ForeignKey("perception_runs.id"),
            nullable=True,
        ),
        sa.Column(
            "contextual_interpretation_run_id",
            sa.Uuid(),
            sa.ForeignKey("contextual_interpretation_runs.id"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "sequence_number > 0",
            name="ck_conversation_turn_sequence_positive",
        ),
        sa.CheckConstraint(
            "(role = 'assistant' AND assistant_text IS NOT NULL AND "
            "length(trim(assistant_text)) > 0 AND utterance_id IS NULL AND "
            "perception_run_id IS NULL AND contextual_interpretation_run_id IS NULL) OR "
            "(role = 'user' AND assistant_text IS NULL AND utterance_id IS NOT NULL AND "
            "perception_run_id IS NOT NULL)",
            name="ck_conversation_turn_role_evidence",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id", "account_id"],
            ["conversations.id", "conversations.account_id"],
            name="fk_conversation_turns_conversation_account",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversation_turns")),
        sa.UniqueConstraint(
            "conversation_id",
            "sequence_number",
            name="uq_conversation_turns_conversation_sequence",
        ),
        sa.UniqueConstraint(
            "perception_run_id",
            name="uq_conversation_turns_perception_run_id",
        ),
        sa.UniqueConstraint(
            "contextual_interpretation_run_id",
            name="uq_conversation_turns_contextual_interpretation_run_id",
        ),
    )
    for column in (
        "account_id",
        "conversation_id",
        "utterance_id",
        "perception_run_id",
        "contextual_interpretation_run_id",
    ):
        op.create_index(
            op.f(f"ix_conversation_turns_{column}"),
            "conversation_turns",
            [column],
        )


def downgrade() -> None:
    op.drop_table("conversation_turns")
    op.drop_table("conversations")

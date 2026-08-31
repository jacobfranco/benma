"""Add append-only assistant generation provenance.

Revision ID: 0008
Revises: 0007
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD_TURN_ROLE_CONSTRAINT = (
    "(role = 'assistant' AND assistant_text IS NOT NULL AND "
    "length(trim(assistant_text)) > 0 AND utterance_id IS NULL AND "
    "perception_run_id IS NULL AND contextual_interpretation_run_id IS NULL) OR "
    "(role = 'user' AND assistant_text IS NULL AND utterance_id IS NOT NULL AND "
    "perception_run_id IS NOT NULL)"
)
TURN_ROLE_CONSTRAINT = (
    "(role = 'assistant' AND assistant_text IS NOT NULL AND "
    "length(trim(assistant_text)) > 0 AND utterance_id IS NULL AND "
    "perception_run_id IS NULL AND contextual_interpretation_run_id IS NULL) OR "
    "(role = 'user' AND assistant_text IS NULL AND utterance_id IS NOT NULL AND "
    "perception_run_id IS NOT NULL AND assistant_generation_run_id IS NULL)"
)


def upgrade() -> None:
    op.create_table(
        "assistant_generation_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column(
            "triggering_user_turn_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("product", sa.String(length=128), nullable=False),
        sa.Column("provider_version", sa.String(length=64), nullable=True),
        sa.Column("adapter_version", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("generator_version", sa.String(length=64), nullable=False),
        sa.Column("generator_configuration", sa.JSON(), nullable=False),
        sa.Column("generation_type", sa.String(length=16), nullable=False),
        sa.Column("input_snapshot", sa.JSON(), nullable=False),
        sa.Column("generated_text", sa.Text(), nullable=True),
        sa.Column("normalized_result", sa.JSON(), nullable=True),
        sa.Column("raw_payload_json", sa.JSON(), nullable=True),
        sa.Column("raw_payload_text", sa.Text(), nullable=True),
        sa.Column("raw_payload_sha256", sa.String(length=64), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "generation_type IN ('reply', 'clarification') AND "
            "status IN ('succeeded', 'failed') AND "
            "((status = 'succeeded' AND generated_text IS NOT NULL AND "
            "length(trim(generated_text)) > 0 AND error_code IS NULL AND "
            "error_message IS NULL) OR "
            "(status = 'failed' AND generated_text IS NULL AND error_code IS NOT NULL))",
            name="ck_assistant_generation_result",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id", "account_id"],
            ["conversations.id", "conversations.account_id"],
            name="fk_assistant_generation_runs_conversation_account",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assistant_generation_runs")),
    )
    for column in ("account_id", "conversation_id", "triggering_user_turn_id"):
        op.create_index(
            op.f(f"ix_assistant_generation_runs_{column}"),
            "assistant_generation_runs",
            [column],
        )

    with op.batch_alter_table("conversation_turns") as batch_op:
        batch_op.add_column(
            sa.Column("assistant_generation_run_id", sa.Uuid(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_conversation_turns_assistant_generation_run_id_assistant_generation_runs",
            "assistant_generation_runs",
            ["assistant_generation_run_id"],
            ["id"],
        )
        batch_op.create_unique_constraint(
            "uq_conversation_turns_assistant_generation_run_id",
            ["assistant_generation_run_id"],
        )
        batch_op.drop_constraint(
            op.f("ck_conversation_turns_ck_conversation_turn_role_evidence"),
            type_="check",
        )
        batch_op.create_check_constraint(
            "ck_conversation_turn_role_evidence",
            TURN_ROLE_CONSTRAINT,
        )
    op.create_index(
        op.f("ix_conversation_turns_assistant_generation_run_id"),
        "conversation_turns",
        ["assistant_generation_run_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_conversation_turns_assistant_generation_run_id"),
        table_name="conversation_turns",
    )
    with op.batch_alter_table("conversation_turns") as batch_op:
        batch_op.drop_constraint(
            op.f("ck_conversation_turns_ck_conversation_turn_role_evidence"),
            type_="check",
        )
        batch_op.create_check_constraint(
            "ck_conversation_turn_role_evidence",
            OLD_TURN_ROLE_CONSTRAINT,
        )
        batch_op.drop_constraint(
            "uq_conversation_turns_assistant_generation_run_id",
            type_="unique",
        )
        batch_op.drop_constraint(
            "fk_conversation_turns_assistant_generation_run_id_assistant_generation_runs",
            type_="foreignkey",
        )
        batch_op.drop_column("assistant_generation_run_id")
    op.drop_table("assistant_generation_runs")

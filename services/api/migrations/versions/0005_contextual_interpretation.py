"""Add append-only contextual interpretation evidence.

Revision ID: 0005
Revises: 0004
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contextual_interpretation_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "account_id", sa.Uuid(), sa.ForeignKey("accounts.id"), nullable=False
        ),
        sa.Column(
            "perception_run_id",
            sa.Uuid(),
            sa.ForeignKey("perception_runs.id"),
            nullable=False,
        ),
        sa.Column("interpreter", sa.String(length=128), nullable=False),
        sa.Column("interpreter_version", sa.String(length=64), nullable=False),
        sa.Column("interpreter_configuration", sa.JSON(), nullable=False),
        sa.Column("context_snapshot", sa.JSON(), nullable=False),
        sa.Column("inferred_text", sa.Text(), nullable=True),
        sa.Column("uncertainty", sa.JSON(), nullable=False),
        sa.Column("clarification_needed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contextual_interpretation_runs")),
    )
    op.create_index(
        op.f("ix_contextual_interpretation_runs_account_id"),
        "contextual_interpretation_runs",
        ["account_id"],
    )
    op.create_index(
        op.f("ix_contextual_interpretation_runs_perception_run_id"),
        "contextual_interpretation_runs",
        ["perception_run_id"],
    )


def downgrade() -> None:
    op.drop_table("contextual_interpretation_runs")

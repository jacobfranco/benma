"""Assessment provider provenance and cost fields.

Revision ID: 0003
Revises: 0002
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("assessment_runs") as batch:
        batch.add_column(
            sa.Column(
                "git_commit_sha",
                sa.String(length=64),
                nullable=False,
                server_default="undocumented",
            )
        )
        batch.add_column(sa.Column("audio_sha256", sa.String(length=64), nullable=True))
        batch.add_column(sa.Column("sample_rate_hz", sa.Integer(), nullable=True))
        batch.add_column(
            sa.Column("request_configuration", sa.JSON(), nullable=False, server_default="{}")
        )
        batch.add_column(
            sa.Column("transport_timings_ms", sa.JSON(), nullable=False, server_default="{}")
        )
        batch.add_column(sa.Column("estimated_billable_units", sa.Float(), nullable=True))
        batch.add_column(sa.Column("estimated_cost_usd", sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("assessment_runs") as batch:
        for column in (
            "estimated_cost_usd",
            "estimated_billable_units",
            "transport_timings_ms",
            "request_configuration",
            "sample_rate_hz",
            "audio_sha256",
            "git_commit_sha",
        ):
            batch.drop_column(column)

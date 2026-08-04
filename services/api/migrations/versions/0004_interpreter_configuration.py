"""Persist interpreter configuration for replay and diff.

Revision ID: 0004_interpreter_configuration
Revises: 0003_assessment_provenance
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "pronunciation_interpretation_runs",
        sa.Column(
            "interpreter_configuration",
            sa.JSON(),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    op.drop_column("pronunciation_interpretation_runs", "interpreter_configuration")

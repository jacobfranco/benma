"""Add an explicit contextual interpretation decision.

Revision ID: 0006
Revises: 0005
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CONSTRAINT_NAME = "ck_contextual_interpretation_decision"
CONSTRAINT_SQL = (
    "decision IN ('preserve', 'infer', 'clarify') AND "
    "((decision = 'clarify' AND clarification_needed) OR "
    "(decision IN ('preserve', 'infer') AND NOT clarification_needed)) AND "
    "(decision != 'infer' OR "
    "(inferred_text IS NOT NULL AND length(trim(inferred_text)) > 0))"
)


def upgrade() -> None:
    op.add_column(
        "contextual_interpretation_runs",
        sa.Column("decision", sa.String(length=16), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE contextual_interpretation_runs "
            "SET decision = CASE "
            "WHEN clarification_needed THEN 'clarify' "
            "WHEN inferred_text IS NOT NULL THEN 'infer' "
            "ELSE 'preserve' END"
        )
    )
    with op.batch_alter_table("contextual_interpretation_runs") as batch_op:
        batch_op.alter_column("decision", existing_type=sa.String(length=16), nullable=False)
        batch_op.create_check_constraint(CONSTRAINT_NAME, CONSTRAINT_SQL)


def downgrade() -> None:
    with op.batch_alter_table("contextual_interpretation_runs") as batch_op:
        batch_op.drop_constraint(CONSTRAINT_NAME, type_="check")
        batch_op.drop_column("decision")

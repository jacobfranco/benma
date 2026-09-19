"""Append transcript-conditioned acoustic evidence without an intended target."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "perceived_speech_analyses",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("utterance_id", sa.Uuid(), sa.ForeignKey("utterances.id"), nullable=False),
        sa.Column(
            "perception_run_id", sa.Uuid(), sa.ForeignKey("perception_runs.id"), nullable=False
        ),
        sa.Column("audio_asset_id", sa.Uuid(), sa.ForeignKey("audio_assets.id"), nullable=False),
        sa.Column("acoustic_run_id", sa.Uuid(), sa.ForeignKey("acoustic_runs.id"), nullable=False),
        sa.Column("audio_sha256", sa.String(64), nullable=False),
        sa.Column("alignment_reference_text", sa.Text(), nullable=False),
        sa.Column("analyzer_version", sa.String(64), nullable=False),
        sa.Column("configuration_sha256", sa.String(64), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "perception_run_id",
            "configuration_sha256",
            name="uq_perceived_analysis_perception_configuration",
        ),
        sa.CheckConstraint(
            "status IN ('succeeded', 'partial', 'failed')", name="ck_perceived_analysis_status"
        ),
    )
    for column in ("account_id", "utterance_id", "perception_run_id"):
        op.create_index(
            op.f(f"ix_perceived_speech_analyses_{column}"), "perceived_speech_analyses", [column]
        )


def downgrade() -> None:
    op.drop_table("perceived_speech_analyses")

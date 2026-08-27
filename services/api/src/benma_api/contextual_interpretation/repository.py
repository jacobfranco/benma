"""Account-scoped persistence for contextual interpretations."""

from __future__ import annotations

import uuid
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from benma_api.db.models import ContextualInterpretationRun, PerceptionRun


class ContextualInterpretationRepository(Protocol):
    def load_perception(
        self, account_id: uuid.UUID, perception_run_id: uuid.UUID
    ) -> PerceptionRun | None: ...
    def append_run(self, run: ContextualInterpretationRun) -> None: ...


class SqlContextualInterpretationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def load_perception(
        self, account_id: uuid.UUID, perception_run_id: uuid.UUID
    ) -> PerceptionRun | None:
        return self.db.scalar(
            select(PerceptionRun).where(
                PerceptionRun.id == perception_run_id,
                PerceptionRun.account_id == account_id,
            )
        )

    def append_run(self, run: ContextualInterpretationRun) -> None:
        self.db.add(run)
        self.db.commit()

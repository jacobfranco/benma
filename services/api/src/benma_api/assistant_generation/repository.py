"""Narrow, account-scoped persistence boundary for assistant generation."""

from __future__ import annotations

import uuid
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from benma_api.db.models import (
    AssistantGenerationRun,
    ContextualInterpretationRun,
    ConversationTurn,
    PerceptionRun,
)

TriggeringTurnEvidence = tuple[
    ConversationTurn,
    PerceptionRun,
    ContextualInterpretationRun,
]


class AssistantGenerationRepository(Protocol):
    def load_triggering_turn_evidence(
        self,
        account_id: uuid.UUID,
        conversation_id: uuid.UUID,
        triggering_user_turn_id: uuid.UUID,
    ) -> TriggeringTurnEvidence | None: ...

    def add_run(self, run: AssistantGenerationRun) -> None: ...

    def commit(self) -> None: ...


class SqlAssistantGenerationRepository:
    """Queries only conversational semantic evidence, never corrections or targets."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def load_triggering_turn_evidence(
        self,
        account_id: uuid.UUID,
        conversation_id: uuid.UUID,
        triggering_user_turn_id: uuid.UUID,
    ) -> TriggeringTurnEvidence | None:
        row = self.db.execute(
            select(ConversationTurn, PerceptionRun, ContextualInterpretationRun)
            .join(
                PerceptionRun,
                PerceptionRun.id == ConversationTurn.perception_run_id,
            )
            .join(
                ContextualInterpretationRun,
                ContextualInterpretationRun.id
                == ConversationTurn.contextual_interpretation_run_id,
            )
            .where(
                ConversationTurn.id == triggering_user_turn_id,
                ConversationTurn.account_id == account_id,
                ConversationTurn.conversation_id == conversation_id,
                ConversationTurn.role == "user",
                PerceptionRun.account_id == account_id,
                PerceptionRun.utterance_id == ConversationTurn.utterance_id,
                ContextualInterpretationRun.account_id == account_id,
                ContextualInterpretationRun.perception_run_id == PerceptionRun.id,
            )
        ).one_or_none()
        if row is None:
            return None
        return row[0], row[1], row[2]

    def add_run(self, run: AssistantGenerationRun) -> None:
        self.db.add(run)

    def commit(self) -> None:
        self.db.commit()

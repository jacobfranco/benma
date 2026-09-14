"""Account-scoped persistence boundary for conversational speech evidence."""

from __future__ import annotations

import uuid
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from benma_api.db.models import (
    AssistantGenerationRun,
    AssistantSpeechRun,
    AudioAsset,
    ConversationTurn,
)

AssistantSpeechSource = tuple[AssistantGenerationRun, ConversationTurn]


class AssistantSpeechRepository(Protocol):
    def load_source(
        self,
        account_id: uuid.UUID,
        assistant_generation_run_id: uuid.UUID,
    ) -> AssistantSpeechSource | None: ...

    def latest_for_turn(
        self,
        account_id: uuid.UUID,
        assistant_turn_id: uuid.UUID,
    ) -> AssistantSpeechRun | None: ...

    def add_run(self, run: AssistantSpeechRun) -> None: ...

    def add_audio(self, audio: AudioAsset) -> None: ...

    def flush(self) -> None: ...

    def commit(self) -> None: ...


class SqlAssistantSpeechRepository:
    """Loads only the persisted assistant text and its conversation linkage."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def load_source(
        self,
        account_id: uuid.UUID,
        assistant_generation_run_id: uuid.UUID,
    ) -> AssistantSpeechSource | None:
        row = self.db.execute(
            select(AssistantGenerationRun, ConversationTurn)
            .join(
                ConversationTurn,
                ConversationTurn.assistant_generation_run_id
                == AssistantGenerationRun.id,
            )
            .where(
                AssistantGenerationRun.id == assistant_generation_run_id,
                AssistantGenerationRun.account_id == account_id,
                AssistantGenerationRun.status == "succeeded",
                ConversationTurn.account_id == account_id,
                ConversationTurn.conversation_id
                == AssistantGenerationRun.conversation_id,
                ConversationTurn.role == "assistant",
                ConversationTurn.assistant_text
                == AssistantGenerationRun.generated_text,
            )
        ).one_or_none()
        if row is None:
            return None
        return row[0], row[1]

    def latest_for_turn(
        self,
        account_id: uuid.UUID,
        assistant_turn_id: uuid.UUID,
    ) -> AssistantSpeechRun | None:
        return self.db.scalar(
            select(AssistantSpeechRun)
            .where(
                AssistantSpeechRun.account_id == account_id,
                AssistantSpeechRun.assistant_turn_id == assistant_turn_id,
            )
            .order_by(AssistantSpeechRun.created_at.desc(), AssistantSpeechRun.id.desc())
            .limit(1)
        )

    def add_run(self, run: AssistantSpeechRun) -> None:
        self.db.add(run)

    def add_audio(self, audio: AudioAsset) -> None:
        self.db.add(audio)

    def flush(self) -> None:
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()

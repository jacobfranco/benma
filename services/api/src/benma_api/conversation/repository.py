"""Account-scoped persistence operations for conversations and their turns."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from benma_api.db.models import Conversation, ConversationTurn, PerceptionRun, Utterance


class SqlConversationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def load_conversation(
        self,
        account_id: uuid.UUID,
        conversation_id: uuid.UUID,
        *,
        for_update: bool = False,
    ) -> Conversation | None:
        query = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.account_id == account_id,
        )
        if for_update:
            query = query.with_for_update()
        return self.db.scalar(query)

    def load_user_evidence(
        self,
        account_id: uuid.UUID,
        *,
        utterance_id: uuid.UUID,
        perception_run_id: uuid.UUID,
    ) -> tuple[Utterance, PerceptionRun] | None:
        row = self.db.execute(
            select(Utterance, PerceptionRun)
            .join(PerceptionRun, PerceptionRun.utterance_id == Utterance.id)
            .where(
                Utterance.id == utterance_id,
                Utterance.account_id == account_id,
                PerceptionRun.id == perception_run_id,
                PerceptionRun.account_id == account_id,
            )
        ).one_or_none()
        if row is None:
            return None
        return row[0], row[1]

    def perception_is_linked(self, perception_run_id: uuid.UUID) -> bool:
        return (
            self.db.scalar(
                select(ConversationTurn.id).where(
                    ConversationTurn.perception_run_id == perception_run_id
                )
            )
            is not None
        )

    def next_sequence_number(self, conversation_id: uuid.UUID) -> int:
        latest = self.db.scalar(
            select(func.max(ConversationTurn.sequence_number)).where(
                ConversationTurn.conversation_id == conversation_id
            )
        )
        return (latest or 0) + 1

    def list_turns(
        self, account_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> list[ConversationTurn]:
        return list(
            self.db.scalars(
                select(ConversationTurn)
                .where(
                    ConversationTurn.account_id == account_id,
                    ConversationTurn.conversation_id == conversation_id,
                )
                .order_by(ConversationTurn.sequence_number.asc())
            )
        )

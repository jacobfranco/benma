"""Transactional orchestration for persisted Free Talk turns."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from benma_api.assistant_generation.contracts import AssistantResponseGenerationPort
from benma_api.assistant_generation.repository import SqlAssistantGenerationRepository
from benma_api.assistant_generation.service import AssistantGenerationService
from benma_api.contextual_interpretation.contracts import ContextualInterpretationPort
from benma_api.contextual_interpretation.repository import (
    SqlContextualInterpretationRepository,
)
from benma_api.contextual_interpretation.service import ContextualInterpretationService
from benma_api.conversation.context import ConversationContextBuilder
from benma_api.conversation.repository import SqlConversationRepository
from benma_api.db.models import Conversation, ConversationTurn, utcnow
from benma_api.errors import (
    AnalysisUnsupportedError,
    AuthorizationError,
    InvalidConversationTurnError,
)


class ConversationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = SqlConversationRepository(db)

    def create(self, *, account_id: uuid.UUID) -> Conversation:
        conversation = Conversation(account_id=account_id)
        self.db.add(conversation)
        self.db.commit()
        return conversation

    def add_assistant_turn(
        self,
        *,
        account_id: uuid.UUID,
        conversation_id: uuid.UUID,
        text: str,
    ) -> ConversationTurn:
        if not text.strip():
            raise InvalidConversationTurnError("assistant turn text cannot be empty")
        conversation = self._load_for_append(account_id, conversation_id)
        turn = ConversationTurn(
            conversation_id=conversation.id,
            account_id=account_id,
            sequence_number=self.repository.next_sequence_number(conversation.id),
            role="assistant",
            assistant_text=text,
        )
        conversation.updated_at = utcnow()
        self.db.add(turn)
        self.db.commit()
        return turn

    def add_user_turn(
        self,
        *,
        account_id: uuid.UUID,
        conversation_id: uuid.UUID,
        utterance_id: uuid.UUID,
        perception_run_id: uuid.UUID,
        interpreter: ContextualInterpretationPort,
        generator: AssistantResponseGenerationPort,
    ) -> ConversationTurn:
        conversation = self._load_for_append(account_id, conversation_id)
        evidence = self.repository.load_user_evidence(
            account_id,
            utterance_id=utterance_id,
            perception_run_id=perception_run_id,
        )
        if evidence is None:
            raise AuthorizationError("utterance or perception run was not found")
        _, perception = evidence
        if perception.transcript is None:
            raise AnalysisUnsupportedError("perception run has no transcript to interpret")
        if self.repository.perception_is_linked(perception_run_id):
            raise InvalidConversationTurnError(
                "perception run is already linked to a conversation turn"
            )

        sequence_number = self.repository.next_sequence_number(conversation.id)
        context_snapshot = ConversationContextBuilder(self.db).build(
            account_id=account_id,
            conversation=conversation,
            before_sequence_number=sequence_number,
        )
        interpretation = ContextualInterpretationService(
            SqlContextualInterpretationRepository(self.db)
        ).build_run(
            account_id=account_id,
            perception_run_id=perception_run_id,
            context_snapshot=context_snapshot,
            interpreter=interpreter,
        )
        self.db.add(interpretation)
        self.db.flush()
        turn = ConversationTurn(
            conversation_id=conversation.id,
            account_id=account_id,
            sequence_number=sequence_number,
            role="user",
            utterance_id=utterance_id,
            perception_run_id=perception_run_id,
            contextual_interpretation_run_id=interpretation.id,
        )
        conversation.updated_at = utcnow()
        self.db.add(turn)
        self.db.flush()

        generation_run = AssistantGenerationService(
            SqlAssistantGenerationRepository(self.db)
        ).run(
            account_id=account_id,
            conversation_id=conversation.id,
            triggering_user_turn_id=turn.id,
            generator=generator,
        )
        self.db.flush()
        assert generation_run.generated_text is not None
        assistant_turn = ConversationTurn(
            conversation_id=conversation.id,
            account_id=account_id,
            sequence_number=sequence_number + 1,
            role="assistant",
            assistant_text=generation_run.generated_text,
            assistant_generation_run_id=generation_run.id,
        )
        conversation.updated_at = utcnow()
        self.db.add(assistant_turn)
        self.db.commit()
        return turn

    def _load_for_append(
        self, account_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> Conversation:
        conversation = self.repository.load_conversation(
            account_id, conversation_id, for_update=True
        )
        if conversation is None:
            raise AuthorizationError("conversation was not found")
        return conversation

"""Transactional orchestration for persisted Free Talk turns."""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy.orm import Session

from benma_api.assistant_generation.contracts import AssistantResponseGenerationPort
from benma_api.assistant_generation.repository import SqlAssistantGenerationRepository
from benma_api.assistant_generation.service import AssistantGenerationService
from benma_api.audio.presence import require_speech
from benma_api.contextual_interpretation.contracts import ContextualInterpretationPort
from benma_api.contextual_interpretation.repository import (
    SqlContextualInterpretationRepository,
)
from benma_api.contextual_interpretation.service import ContextualInterpretationService
from benma_api.conversation.context import ConversationContextBuilder
from benma_api.conversation.repository import SqlConversationRepository
from benma_api.db.models import (
    AudioAsset,
    ContextualInterpretationRun,
    Conversation,
    ConversationTurn,
    utcnow,
)
from benma_api.errors import (
    AnalysisUnsupportedError,
    AuthorizationError,
    InvalidConversationTurnError,
)
from benma_api.storage.audio_store import AudioObjectStore


@dataclass(frozen=True, slots=True)
class FreeTalkTurnResult:
    user_turn: ConversationTurn
    assistant_turn: ConversationTurn
    interpretation_ms: int
    generation_ms: int


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
        store: AudioObjectStore,
        on_interpretation: Callable[[ContextualInterpretationRun, int], None] | None = None,
    ) -> FreeTalkTurnResult:
        conversation = self._load_for_append(account_id, conversation_id)
        evidence = self.repository.load_user_evidence(
            account_id,
            utterance_id=utterance_id,
            perception_run_id=perception_run_id,
        )
        if evidence is None:
            raise AuthorizationError("utterance or perception run was not found")
        utterance, perception = evidence
        if perception.status != "succeeded" or not (perception.transcript or "").strip():
            raise AnalysisUnsupportedError("perception run has no transcript to interpret")
        asset = self.db.get(AudioAsset, utterance.canonical_audio_asset_id)
        if asset is None or asset.account_id != account_id:
            raise AuthorizationError("canonical audio was not found")
        require_speech(store.read(asset.storage_key), transcript=perception.transcript)
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
        started = time.perf_counter()
        interpretation = ContextualInterpretationService(
            SqlContextualInterpretationRepository(self.db)
        ).build_run(
            account_id=account_id,
            perception_run_id=perception_run_id,
            context_snapshot=context_snapshot,
            interpreter=interpreter,
        )
        interpretation_ms = round((time.perf_counter() - started) * 1000)
        self.db.add(interpretation)
        self.db.flush()
        if on_interpretation is not None:
            on_interpretation(interpretation, interpretation_ms)
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

        generation_run = AssistantGenerationService(SqlAssistantGenerationRepository(self.db)).run(
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
        # Return durable text immediately. Speech is an independent, retryable request
        # against this persisted generation, never client-supplied text.
        self.db.commit()
        return FreeTalkTurnResult(
            user_turn=turn,
            assistant_turn=assistant_turn,
            interpretation_ms=interpretation_ms,
            generation_ms=generation_run.latency_ms or 0,
        )

    def _load_for_append(self, account_id: uuid.UUID, conversation_id: uuid.UUID) -> Conversation:
        conversation = self.repository.load_conversation(
            account_id, conversation_id, for_update=True
        )
        if conversation is None:
            raise AuthorizationError("conversation was not found")
        return conversation

"""Deterministic semantic context derived from prior persisted turns."""

from __future__ import annotations

import uuid
from typing import Any, Literal, TypedDict, cast

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from benma_api.db.models import (
    ContextualInterpretationRun,
    Conversation,
    ConversationTurn,
    PerceptionRun,
)

CONVERSATION_CONTEXT_FORMAT = "benma.conversation-context"
CONVERSATION_CONTEXT_VERSION = 1


class ResolvedContextTurn(TypedDict):
    role: Literal["user", "assistant"]
    text: str


class UnresolvedContextTurn(TypedDict):
    role: Literal["user"]
    unresolved: Literal[True]


def resolved_user_turn_text(
    *,
    perceived_transcript: str | None,
    decision: str | None,
    inferred_text: str | None,
) -> str | None:
    """Resolve downstream user semantics without changing perception evidence."""
    if decision is None or decision == "clarify":
        return None
    if decision == "preserve":
        return perceived_transcript
    if decision == "infer":
        if inferred_text is None:
            raise ValueError("infer decisions require inferred text")
        return inferred_text
    raise ValueError("contextual interpretation decision is invalid")


def resolved_turn_text(
    turn: ConversationTurn,
    *,
    perception: PerceptionRun | None = None,
    interpretation: ContextualInterpretationRun | None = None,
) -> str | None:
    """Return the semantic text represented by a persisted turn."""
    if turn.role == "assistant":
        if turn.assistant_text is None:
            raise ValueError("assistant turn has no text")
        return turn.assistant_text
    if turn.role != "user":
        raise ValueError("conversation turn role is invalid")
    if perception is None:
        raise ValueError("user turn has no perception evidence")
    return resolved_user_turn_text(
        perceived_transcript=perception.transcript,
        decision=interpretation.decision if interpretation is not None else None,
        inferred_text=interpretation.inferred_text if interpretation is not None else None,
    )


class ConversationContextBuilder:
    """Build a versioned snapshot from explicit semantic fields on prior turns only."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def build(
        self,
        *,
        account_id: uuid.UUID,
        conversation: Conversation,
        before_sequence_number: int,
    ) -> dict[str, Any]:
        rows = self.db.execute(
            select(ConversationTurn, PerceptionRun, ContextualInterpretationRun)
            .outerjoin(
                PerceptionRun,
                and_(
                    ConversationTurn.perception_run_id == PerceptionRun.id,
                    PerceptionRun.account_id == account_id,
                ),
            )
            .outerjoin(
                ContextualInterpretationRun,
                and_(
                    ConversationTurn.contextual_interpretation_run_id
                    == ContextualInterpretationRun.id,
                    ContextualInterpretationRun.account_id == account_id,
                    ContextualInterpretationRun.perception_run_id
                    == ConversationTurn.perception_run_id,
                ),
            )
            .where(
                ConversationTurn.account_id == account_id,
                ConversationTurn.conversation_id == conversation.id,
                ConversationTurn.sequence_number < before_sequence_number,
            )
            .order_by(ConversationTurn.sequence_number.asc())
        ).all()
        turns: list[ResolvedContextTurn | UnresolvedContextTurn] = []
        for turn, perception, interpretation in rows:
            text = resolved_turn_text(
                turn,
                perception=perception,
                interpretation=interpretation,
            )
            if text is None:
                turns.append({"role": "user", "unresolved": True})
            else:
                role = cast(Literal["user", "assistant"], turn.role)
                turns.append({"role": role, "text": text})
        return {
            "format": CONVERSATION_CONTEXT_FORMAT,
            "version": CONVERSATION_CONTEXT_VERSION,
            "turns": turns,
        }

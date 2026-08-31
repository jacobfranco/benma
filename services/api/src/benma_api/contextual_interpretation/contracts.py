"""Provider-neutral contracts for contextual interpretation execution."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Literal, Protocol

ContextualInterpretationDecision = Literal["preserve", "infer", "clarify"]


@dataclass(frozen=True, slots=True)
class ContextualInterpretationInput:
    """Immutable perceived text plus downstream semantic context."""

    perception_run_id: uuid.UUID
    perceived_transcript: str
    perception_evidence_snapshot: dict[str, Any]
    context_snapshot: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ContextualInterpretationEvidence:
    decision: ContextualInterpretationDecision
    inferred_text: str | None
    uncertainty: dict[str, Any]
    clarification_needed: bool

    def __post_init__(self) -> None:
        validate_contextual_interpretation_evidence(self)


def validate_contextual_interpretation_evidence(
    evidence: ContextualInterpretationEvidence,
    *,
    perceived_transcript: str | None = None,
) -> None:
    """Reject contradictory decisions at the provider-neutral boundary."""
    if evidence.decision not in {"preserve", "infer", "clarify"}:
        raise ValueError("contextual interpretation decision is invalid")
    if evidence.inferred_text is not None and not evidence.inferred_text.strip():
        raise ValueError("contextual inferred_text cannot be empty")
    if evidence.decision == "clarify":
        if not evidence.clarification_needed:
            raise ValueError("clarify decisions must request clarification")
    elif evidence.clarification_needed:
        raise ValueError("preserve and infer decisions cannot request clarification")
    if evidence.decision == "infer" and evidence.inferred_text is None:
        raise ValueError("infer decisions must include inferred_text")
    if perceived_transcript is None:
        return
    if evidence.decision == "preserve" and evidence.inferred_text not in {
        None,
        perceived_transcript,
    }:
        raise ValueError("preserve inferred_text must be absent or match the perceived transcript")
    if evidence.decision == "infer" and evidence.inferred_text == perceived_transcript:
        raise ValueError("infer decisions must differ from the perceived transcript")


class ContextualInterpretationPort(Protocol):
    """Abstract interpreter boundary; an LLM adapter may implement this later."""

    interpreter_name: str
    interpreter_version: str
    interpreter_configuration: dict[str, Any]

    def interpret(
        self, request: ContextualInterpretationInput
    ) -> ContextualInterpretationEvidence: ...

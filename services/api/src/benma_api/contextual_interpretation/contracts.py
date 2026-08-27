"""Provider-neutral contracts for contextual interpretation execution."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class ContextualInterpretationInput:
    """Immutable perceived text plus downstream semantic context."""

    perception_run_id: uuid.UUID
    perceived_transcript: str
    perception_evidence_snapshot: dict[str, Any]
    context_snapshot: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ContextualInterpretationEvidence:
    inferred_text: str | None
    uncertainty: dict[str, Any]
    clarification_needed: bool


class ContextualInterpretationPort(Protocol):
    """Abstract interpreter boundary; an LLM adapter may implement this later."""

    interpreter_name: str
    interpreter_version: str
    interpreter_configuration: dict[str, Any]

    def interpret(
        self, request: ContextualInterpretationInput
    ) -> ContextualInterpretationEvidence: ...

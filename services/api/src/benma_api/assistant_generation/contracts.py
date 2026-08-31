"""Provider-neutral contracts for assistant response generation."""

from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from benma_api.contextual_interpretation.contracts import ContextualInterpretationDecision

AssistantGenerationType = Literal["reply", "clarification"]

ASSISTANT_GENERATION_INPUT_FORMAT = "benma.assistant-generation-input"
ASSISTANT_GENERATION_INPUT_VERSION = 1


@dataclass(frozen=True, slots=True)
class AssistantResponseGenerationInput:
    """Semantic evidence for one response, assembled only from persisted server state."""

    conversation_context_snapshot: dict[str, Any]
    perceived_transcript: str
    contextual_decision: ContextualInterpretationDecision
    resolved_semantic_text: str | None
    clarification_alternatives: tuple[str, ...]
    generation_type: AssistantGenerationType

    def __post_init__(self) -> None:
        validate_assistant_generation_input(self)

    def snapshot(self) -> dict[str, Any]:
        """Return the exact provider-visible semantic input in a versioned envelope."""
        return {
            "format": ASSISTANT_GENERATION_INPUT_FORMAT,
            "version": ASSISTANT_GENERATION_INPUT_VERSION,
            "conversation_context": deepcopy(self.conversation_context_snapshot),
            "current_user_turn": {
                "perceived_transcript": self.perceived_transcript,
                "contextual_decision": self.contextual_decision,
                "resolved_semantic_text": self.resolved_semantic_text,
                "clarification_alternatives": list(self.clarification_alternatives),
            },
            "generation_type": self.generation_type,
        }


def validate_assistant_generation_input(request: AssistantResponseGenerationInput) -> None:
    """Enforce reply-versus-clarification semantics before any provider call."""
    perceived = request.perceived_transcript.strip()
    resolved = (
        request.resolved_semantic_text.strip()
        if request.resolved_semantic_text is not None
        else None
    )
    if not perceived:
        raise ValueError("assistant generation requires a perceived transcript")
    if any(
        not isinstance(candidate, str)
        or not candidate.strip()
        or candidate != candidate.strip()
        for candidate in request.clarification_alternatives
    ):
        raise ValueError("clarification alternatives must be normalized non-empty strings")
    if len(set(request.clarification_alternatives)) != len(
        request.clarification_alternatives
    ):
        raise ValueError("clarification alternatives must be unique")
    if request.contextual_decision == "clarify":
        if request.generation_type != "clarification":
            raise ValueError("clarify decisions require clarification generation")
        if resolved is not None:
            raise ValueError("clarify decisions cannot have resolved semantic text")
        return
    if request.clarification_alternatives:
        raise ValueError("reply generation cannot receive clarification alternatives")
    if request.generation_type != "reply":
        raise ValueError("preserve and infer decisions require reply generation")
    if resolved is None or not resolved:
        raise ValueError("reply generation requires resolved semantic text")
    if request.contextual_decision == "preserve" and resolved != perceived:
        raise ValueError("preserve replies must answer the perceived transcript")
    if request.contextual_decision == "infer" and resolved == perceived:
        raise ValueError("infer replies must answer a distinct inferred meaning")


@dataclass(frozen=True, slots=True)
class AssistantResponseGenerationEvidence:
    generation_type: AssistantGenerationType
    generated_text: str
    clarification_alternatives_used: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.generation_type not in {"reply", "clarification"}:
            raise ValueError("assistant generation type is invalid")
        if not self.generated_text.strip():
            raise ValueError("assistant generated text cannot be empty")
        if any(
            not isinstance(candidate, str)
            or not candidate.strip()
            or candidate != candidate.strip()
            for candidate in self.clarification_alternatives_used
        ):
            raise ValueError("used clarification alternatives must be normalized strings")
        if len(set(self.clarification_alternatives_used)) != len(
            self.clarification_alternatives_used
        ):
            raise ValueError("used clarification alternatives must be unique")

    def normalized(self) -> dict[str, str | list[str]]:
        return {
            "generation_type": self.generation_type,
            "generated_text": self.generated_text,
            "clarification_alternatives_used": list(
                self.clarification_alternatives_used
            ),
        }


_QUOTED_PHRASE_PATTERNS = (
    re.compile(r'"([^"\n]+)"'),
    re.compile(r"“([^”\n]+)”"),
    re.compile(r"「([^」\n]+)」"),
    re.compile(r"『([^』\n]+)』"),
)


def quotation_delimited_phrases(text: str) -> tuple[str, ...]:
    """Extract obvious quoted candidate-like spans without interpreting Mandarin semantics."""
    phrases: list[str] = []
    for pattern in _QUOTED_PHRASE_PATTERNS:
        phrases.extend(match.group(1).strip() for match in pattern.finditer(text))
    return tuple(phrase for phrase in phrases if phrase)


def validate_assistant_generation_evidence(
    evidence: AssistantResponseGenerationEvidence,
    *,
    request: AssistantResponseGenerationInput,
) -> None:
    """Ground declared and obvious quoted clarification candidates in the input allowlist.

    This catches structured-output violations and quotation-delimited candidate injection. It
    cannot prove that arbitrary unquoted natural language contains no implicit candidate phrase.
    """
    if evidence.generation_type != request.generation_type:
        raise ValueError("provider returned the wrong assistant generation type")
    used = evidence.clarification_alternatives_used
    if request.generation_type == "reply":
        if used:
            raise ValueError("reply output cannot use clarification alternatives")
        return
    allowed = set(request.clarification_alternatives)
    if any(candidate not in allowed for candidate in used):
        raise ValueError("clarification output used a non-allowlisted alternative")
    if any(candidate not in evidence.generated_text for candidate in used):
        raise ValueError("declared clarification alternative is absent from generated text")
    quoted = quotation_delimited_phrases(evidence.generated_text)
    if any(candidate not in used for candidate in quoted):
        raise ValueError("clarification output contains an undeclared quoted candidate")


@dataclass(frozen=True, slots=True)
class AssistantGenerationProviderResponse:
    evidence: AssistantResponseGenerationEvidence
    raw_payload: object
    provider_version: str | None = None


class AssistantResponseGenerationPort(Protocol):
    provider_name: str
    product_name: str
    adapter_version: str
    generator_version: str
    generator_configuration: dict[str, Any]

    def generate(
        self, request: AssistantResponseGenerationInput
    ) -> AssistantGenerationProviderResponse: ...

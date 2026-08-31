"""Allowlisted contextual interpreter selection."""

from __future__ import annotations

from benma_api.config import Settings
from benma_api.contextual_interpretation.contracts import ContextualInterpretationPort
from benma_api.contextual_interpretation.openai import OpenAIContextualInterpreter
from benma_api.errors import AnalysisUnsupportedError


def build_contextual_interpreter(settings: Settings) -> ContextualInterpretationPort:
    if settings.contextual_interpretation_provider == "openai":
        assert settings.openai_api_key is not None
        return OpenAIContextualInterpreter(
            settings.openai_api_key.get_secret_value(),
            model=settings.openai_contextual_interpretation_model,
            timeout_seconds=settings.contextual_interpretation_timeout_seconds,
            interpreter_version=settings.contextual_interpretation_version,
            reasoning_effort=(settings.openai_contextual_interpretation_reasoning_effort),
        )
    raise AnalysisUnsupportedError("contextual interpretation provider is not configured")

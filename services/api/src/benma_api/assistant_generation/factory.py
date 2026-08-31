"""Allowlisted assistant response generator selection."""

from __future__ import annotations

from benma_api.assistant_generation.contracts import AssistantResponseGenerationPort
from benma_api.assistant_generation.openai import OpenAIAssistantResponseGenerator
from benma_api.config import Settings
from benma_api.errors import AnalysisUnsupportedError


def build_assistant_response_generator(
    settings: Settings,
) -> AssistantResponseGenerationPort:
    if settings.assistant_generation_provider == "openai":
        assert settings.openai_api_key is not None
        return OpenAIAssistantResponseGenerator(
            settings.openai_api_key.get_secret_value(),
            model=settings.openai_assistant_generation_model,
            timeout_seconds=settings.assistant_generation_timeout_seconds,
            generator_version=settings.assistant_generation_policy_version,
            reasoning_effort=settings.openai_assistant_generation_reasoning_effort,
        )
    raise AnalysisUnsupportedError("assistant generation provider is not configured")

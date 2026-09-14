"""Allowlisted conversational speech provider selection."""

from __future__ import annotations

from benma_api.config import Settings
from benma_api.speech.synthesis import (
    AzureSpeechSynthesisProvider,
    DisabledSpeechSynthesisProvider,
    SpeechSynthesisPort,
)


def build_assistant_speech_provider(settings: Settings) -> SpeechSynthesisPort:
    if settings.assistant_speech_provider == "azure":
        assert settings.azure_speech_key is not None
        assert settings.azure_speech_region is not None
        return AzureSpeechSynthesisProvider(
            settings.azure_speech_key.get_secret_value(),
            settings.azure_speech_region,
        )
    return DisabledSpeechSynthesisProvider()

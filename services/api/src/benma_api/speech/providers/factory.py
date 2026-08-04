"""Allowlisted provider configuration; strings never import arbitrary classes."""

from __future__ import annotations

from benma_api.config import Settings
from benma_api.errors import AnalysisUnsupportedError
from benma_api.speech.contracts import PerceptionPort, PronunciationAssessmentPort
from benma_api.speech.providers.azure import AzurePronunciationProvider
from benma_api.speech.providers.iflytek import IflytekIsePronunciationProvider
from benma_api.speech.providers.openai import OpenAITranscriptionProvider
from benma_api.speech.providers.replay import (
    ReplayPerceptionProvider,
    ReplayPronunciationProvider,
)
from benma_api.speech.providers.tencent import TencentSoenPronunciationProvider


class DisabledPerceptionProvider:
    provider_name = "disabled"
    product_name = "disabled"
    adapter_version = "1.0.0"

    def perceive(self, request):  # type: ignore[no-untyped-def]
        raise AnalysisUnsupportedError("unknown-target perception is not configured")


class DisabledAssessmentProvider:
    provider_name = "disabled"
    product_name = "disabled"
    adapter_version = "1.0.0"

    def assess(self, request):  # type: ignore[no-untyped-def]
        raise AnalysisUnsupportedError("pronunciation assessment is not configured")


def build_perception_provider(settings: Settings) -> PerceptionPort:
    if settings.perception_provider == "replay":
        return ReplayPerceptionProvider()
    if settings.perception_provider == "openai":
        assert settings.openai_api_key is not None
        return OpenAITranscriptionProvider(
            settings.openai_api_key.get_secret_value(), settings.openai_transcription_model
        )
    return DisabledPerceptionProvider()


def build_assessment_provider(settings: Settings) -> PronunciationAssessmentPort:
    if settings.assessment_provider == "replay":
        return ReplayPronunciationProvider()
    if settings.assessment_provider == "azure":
        assert settings.azure_speech_key is not None
        assert settings.azure_speech_region is not None
        return AzurePronunciationProvider(
            settings.azure_speech_key.get_secret_value(), settings.azure_speech_region
        )
    if settings.assessment_provider in {"tencent_sentence", "tencent_pinyin"}:
        assert settings.tencent_secret_id is not None
        assert settings.tencent_secret_key is not None
        assert settings.tencent_soe_app_id is not None
        return TencentSoenPronunciationProvider(
            settings.tencent_secret_id.get_secret_value(),
            settings.tencent_secret_key.get_secret_value(),
            settings.tencent_soe_app_id,
            mode=(
                "sentence" if settings.assessment_provider == "tencent_sentence" else "pinyin"
            ),
            score_coeff=settings.tencent_soe_score_coeff,
            configured_timeout_seconds=settings.tencent_soe_timeout_seconds,
        )
    if settings.assessment_provider == "iflytek":
        assert settings.iflytek_app_id is not None
        assert settings.iflytek_api_key is not None
        assert settings.iflytek_api_secret is not None
        return IflytekIsePronunciationProvider(
            settings.iflytek_app_id,
            settings.iflytek_api_key.get_secret_value(),
            settings.iflytek_api_secret.get_secret_value(),
            configured_timeout_seconds=settings.iflytek_ise_timeout_seconds,
        )
    return DisabledAssessmentProvider()

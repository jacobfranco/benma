"""Typed, fail-fast application configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "production"]
PerceptionProviderName = Literal["replay", "openai", "disabled"]
AssessmentProviderName = Literal[
    "replay",
    "azure",
    "tencent_sentence",
    "tencent_pinyin",
    "iflytek",
    "disabled",
]
ReferenceSpeechProviderName = Literal["replay", "azure", "disabled"]
AssistantSpeechProviderName = Literal["azure", "disabled"]
AcousticProviderName = Literal["praat", "autocorrelation", "disabled"]
AlignmentProviderName = Literal["auto", "azure", "replay", "mfa", "disabled"]
ContextualInterpretationProviderName = Literal["openai", "disabled"]
AssistantGenerationProviderName = Literal["openai", "disabled"]
OpenAIReasoningEffort = Literal["none", "low", "medium", "high"]
DEVELOPMENT_CORS_ORIGINS = ("http://localhost:8081", "http://127.0.0.1:8081")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BENMA_", env_file=".env", extra="forbid", case_sensitive=False
    )

    environment: Environment = "development"
    database_url: str = "postgresql+psycopg://benma:benma@localhost:5432/benma"
    audio_storage_dir: Path = Path("var/audio")
    dev_auth_enabled: bool = False
    cors_allowed_origins: list[AnyHttpUrl] = Field(default_factory=list)
    session_ttl_days: int = 30
    max_upload_bytes: int = 15 * 1024 * 1024
    max_audio_duration_seconds: float = 120.0
    ffmpeg_binary: str = "ffmpeg"
    ffprobe_binary: str = "ffprobe"

    perception_provider: PerceptionProviderName = "disabled"
    assessment_provider: AssessmentProviderName = "disabled"
    reference_speech_provider: ReferenceSpeechProviderName = "disabled"
    assistant_speech_provider: AssistantSpeechProviderName = "disabled"
    acoustic_provider: AcousticProviderName = "praat"
    alignment_provider: AlignmentProviderName = "auto"
    # Explicit paid timing opt-in. Possessing a TTS/assessment credential is insufficient.
    azure_alignment_enabled: bool = False
    alignment_timeout_seconds: float = 12.0
    contextual_interpretation_provider: ContextualInterpretationProviderName = "disabled"
    assistant_generation_provider: AssistantGenerationProviderName = "disabled"
    openai_api_key: SecretStr | None = None
    openai_transcription_model: str = "gpt-4o-transcribe"
    openai_contextual_interpretation_model: str = "gpt-5.6-terra"
    openai_contextual_interpretation_reasoning_effort: OpenAIReasoningEffort = "medium"
    contextual_interpretation_timeout_seconds: float = 30.0
    contextual_interpretation_version: str = "contextual-decision-v1"
    openai_assistant_generation_model: str = "gpt-5.6-terra"
    openai_assistant_generation_reasoning_effort: OpenAIReasoningEffort = "medium"
    assistant_generation_timeout_seconds: float = 30.0
    assistant_generation_policy_version: str = "free-talk-generation-v1"
    assistant_speech_voice: str = "zh-CN-Xiaochen:DragonHDFlashLatestNeural"
    assistant_speech_locale: str = "zh-CN"
    assistant_speech_model_version: str = "DragonHDFlashLatestNeural"
    assistant_speech_rate: str = "0%"
    assistant_speech_timeout_seconds: float = 30.0
    azure_speech_key: SecretStr | None = None
    azure_speech_region: str | None = None
    tencent_secret_id: SecretStr | None = None
    tencent_secret_key: SecretStr | None = None
    tencent_soe_app_id: str | None = None
    tencent_soe_score_coeff: float = 4.0
    tencent_soe_timeout_seconds: float = 30.0
    iflytek_app_id: str | None = None
    iflytek_api_key: SecretStr | None = None
    iflytek_api_secret: SecretStr | None = None
    iflytek_ise_timeout_seconds: float = 45.0
    reference_speech_voice: str = "zh-CN-Xiaochen:DragonHDLatestNeural"
    reference_speech_model_version: str = "DragonHDLatestNeural"
    reference_speech_rate: str = "0%"
    mfa_binary: str = "mfa"
    mfa_dictionary: str = "mandarin_mfa"
    mfa_acoustic_model: str = "mandarin_mfa"
    mfa_timeout_seconds: float = 45.0
    enable_experimental_tone_interpretation: bool = False
    enable_dev_learned_tone: bool = False
    enable_categorical_tone_judgment: bool = False

    @field_validator("cors_allowed_origins")
    @classmethod
    def validate_cors_origins(cls, origins: list[AnyHttpUrl]) -> list[AnyHttpUrl]:
        for origin in origins:
            if (
                not origin.host
                or "*" in origin.host
                or origin.username is not None
                or origin.password is not None
                or origin.path not in (None, "", "/")
                or origin.query is not None
                or origin.fragment is not None
            ):
                raise ValueError("CORS origins must contain only an HTTP(S) scheme, host, and port")
        return origins

    @property
    def effective_cors_origins(self) -> list[str]:
        defaults = DEVELOPMENT_CORS_ORIGINS if self.environment == "development" else ()
        # URL validation normalizes host/default ports; an Origin header has no trailing slash.
        configured = [str(origin).removesuffix("/") for origin in self.cors_allowed_origins]
        return list(dict.fromkeys([*defaults, *configured]))

    @model_validator(mode="after")
    def validate_environment(self) -> Self:
        if self.enable_dev_learned_tone:
            if self.environment == "production":
                raise ValueError("learned tone is development-only")
            if self.alignment_provider not in {"auto", "azure"}:
                raise ValueError("learned dev tone requires Azure timing; MFA is research-only")
            if not (self.alignment_provider == "azure" or self.azure_alignment_enabled):
                raise ValueError("learned dev tone requires explicit Azure timing opt-in")
            if self.acoustic_provider != "praat":
                raise ValueError("learned dev tone requires the frozen Praat frontend")
        if self.alignment_timeout_seconds <= 0:
            raise ValueError("alignment timeout must be positive")
        if (self.alignment_provider == "azure" or self.azure_alignment_enabled) and (
            not self.azure_speech_key or not self.azure_speech_region
        ):
            raise ValueError("Azure credentials are required for explicitly enabled timing")
        if self.environment == "production" and self.dev_auth_enabled:
            raise ValueError("development authentication cannot be enabled in production")
        if self.max_upload_bytes <= 0 or self.max_audio_duration_seconds <= 0:
            raise ValueError("audio limits must be positive")
        if (
            self.perception_provider == "openai"
            or self.contextual_interpretation_provider == "openai"
            or self.assistant_generation_provider == "openai"
        ) and not self.openai_api_key:
            raise ValueError("BENMA_OPENAI_API_KEY is required for the OpenAI provider")
        if self.contextual_interpretation_timeout_seconds <= 0:
            raise ValueError("contextual interpretation timeout must be positive")
        if not self.openai_contextual_interpretation_model.strip():
            raise ValueError("OpenAI contextual interpretation model cannot be empty")
        if not self.contextual_interpretation_version.strip():
            raise ValueError("contextual interpretation version cannot be empty")
        if self.assistant_generation_timeout_seconds <= 0:
            raise ValueError("assistant generation timeout must be positive")
        if not self.openai_assistant_generation_model.strip():
            raise ValueError("OpenAI assistant generation model cannot be empty")
        if not self.assistant_generation_policy_version.strip():
            raise ValueError("assistant generation policy version cannot be empty")
        if self.assistant_speech_timeout_seconds <= 0:
            raise ValueError("assistant speech timeout must be positive")
        if not all(
            value.strip()
            for value in (
                self.assistant_speech_voice,
                self.assistant_speech_locale,
                self.assistant_speech_model_version,
                self.assistant_speech_rate,
            )
        ):
            raise ValueError("assistant speech configuration cannot contain empty values")
        if self.assessment_provider == "azure" and (
            not self.azure_speech_key or not self.azure_speech_region
        ):
            raise ValueError("Azure speech key and region are required for the Azure provider")
        if self.assessment_provider in {"tencent_sentence", "tencent_pinyin"} and (
            not self.tencent_secret_id
            or not self.tencent_secret_key
            or not self.tencent_soe_app_id
        ):
            raise ValueError(
                "Tencent SOE-N SecretId, SecretKey, and AppID are required; "
                "the legacy Basic product is not supported"
            )
        if not 1.0 <= self.tencent_soe_score_coeff <= 4.0:
            raise ValueError("Tencent SOE-N score coefficient must be between 1.0 and 4.0")
        if self.tencent_soe_timeout_seconds <= 0 or self.iflytek_ise_timeout_seconds <= 0:
            raise ValueError("provider timeouts must be positive")
        if self.assessment_provider == "iflytek" and (
            not self.iflytek_app_id or not self.iflytek_api_key or not self.iflytek_api_secret
        ):
            raise ValueError(
                "iFlytek streaming ISE AppID, APIKey, and APISecret are required"
            )
        if self.reference_speech_provider == "azure" and (
            not self.azure_speech_key or not self.azure_speech_region
        ):
            raise ValueError("Azure speech key and region are required for reference speech")
        if self.assistant_speech_provider == "azure" and (
            not self.azure_speech_key or not self.azure_speech_region
        ):
            raise ValueError("Azure speech key and region are required for assistant speech")
        if self.enable_categorical_tone_judgment:
            raise ValueError(
                "categorical tone judgment cannot be enabled before calibration policy exists"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


async def get_request_settings() -> Settings:
    """Coroutine dependency avoids FastAPI's worker bridge for a cache lookup."""
    return get_settings()

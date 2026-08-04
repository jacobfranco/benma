"""Typed, fail-fast application configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "production"]
PerceptionProviderName = Literal["replay", "openai", "disabled"]
AssessmentProviderName = Literal["replay", "azure", "disabled"]
ReferenceSpeechProviderName = Literal["replay", "azure", "disabled"]
AcousticProviderName = Literal["autocorrelation", "disabled"]
AlignmentProviderName = Literal["replay", "mfa", "disabled"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BENMA_", env_file=".env", extra="forbid", case_sensitive=False
    )

    environment: Environment = "development"
    database_url: str = "postgresql+psycopg://benma:benma@localhost:5432/benma"
    audio_storage_dir: Path = Path("var/audio")
    dev_auth_enabled: bool = False
    session_ttl_days: int = 30
    max_upload_bytes: int = 15 * 1024 * 1024
    max_audio_duration_seconds: float = 120.0
    ffmpeg_binary: str = "ffmpeg"
    ffprobe_binary: str = "ffprobe"

    perception_provider: PerceptionProviderName = "disabled"
    assessment_provider: AssessmentProviderName = "disabled"
    reference_speech_provider: ReferenceSpeechProviderName = "disabled"
    acoustic_provider: AcousticProviderName = "autocorrelation"
    alignment_provider: AlignmentProviderName = "disabled"
    openai_api_key: SecretStr | None = None
    openai_transcription_model: str = "gpt-4o-transcribe"
    azure_speech_key: SecretStr | None = None
    azure_speech_region: str | None = None
    reference_speech_voice: str = "zh-CN-Xiaochen:DragonHDLatestNeural"
    reference_speech_model_version: str = "DragonHDLatestNeural"
    reference_speech_rate: str = "0%"
    mfa_binary: str = "mfa"
    mfa_dictionary: str = "mandarin_mfa"
    mfa_acoustic_model: str = "mandarin_mfa"
    mfa_timeout_seconds: float = 45.0
    enable_experimental_tone_interpretation: bool = True
    enable_categorical_tone_judgment: bool = False

    @model_validator(mode="after")
    def validate_environment(self) -> Self:
        if self.environment == "production" and self.dev_auth_enabled:
            raise ValueError("development authentication cannot be enabled in production")
        if self.max_upload_bytes <= 0 or self.max_audio_duration_seconds <= 0:
            raise ValueError("audio limits must be positive")
        if self.perception_provider == "openai" and not self.openai_api_key:
            raise ValueError("BENMA_OPENAI_API_KEY is required for the OpenAI provider")
        if self.assessment_provider == "azure" and (
            not self.azure_speech_key or not self.azure_speech_region
        ):
            raise ValueError("Azure speech key and region are required for the Azure provider")
        if self.reference_speech_provider == "azure" and (
            not self.azure_speech_key or not self.azure_speech_region
        ):
            raise ValueError("Azure speech key and region are required for reference speech")
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

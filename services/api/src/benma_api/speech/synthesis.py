"""Provider-neutral speech synthesis transport shared by distinct domains."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from xml.sax.saxutils import escape

import httpx

from benma_api.errors import (
    AnalysisUnsupportedError,
    ProviderMalformedResponseError,
    ProviderRejectedError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)


@dataclass(frozen=True, slots=True)
class SpeechSynthesisRequest:
    text: str
    locale: str
    voice: str
    model_version: str
    rate: str
    timeout_seconds: float


@dataclass(frozen=True, slots=True)
class SpeechSynthesisResponse:
    audio: bytes
    mime_type: str
    provider_version: str
    evidence_status: str


class SpeechSynthesisPort(Protocol):
    provider_name: str
    product_name: str
    adapter_version: str

    def synthesize(self, request: SpeechSynthesisRequest) -> SpeechSynthesisResponse: ...


class AzureSpeechSynthesisProvider:
    """Azure REST synthesis without pronunciation or conversation semantics."""

    provider_name = "azure_speech"
    product_name = "speech_synthesis"
    adapter_version = "1.1.0"

    def __init__(
        self,
        key: str,
        region: str,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._key = key
        self._region = region
        self._transport = transport

    def synthesize(self, request: SpeechSynthesisRequest) -> SpeechSynthesisResponse:
        ssml = (
            f'<speak version="1.0" xml:lang="{escape(request.locale)}">'
            f'<voice name="{escape(request.voice)}">'
            f'<prosody rate="{escape(request.rate)}">{escape(request.text)}</prosody>'
            "</voice></speak>"
        )
        try:
            with httpx.Client(
                transport=self._transport,
                timeout=request.timeout_seconds,
            ) as client:
                response = client.post(
                    f"https://{self._region}.tts.speech.microsoft.com/cognitiveservices/v1",
                    headers={
                        "Ocp-Apim-Subscription-Key": self._key,
                        "Content-Type": "application/ssml+xml",
                        "X-Microsoft-OutputFormat": "riff-24khz-16bit-mono-pcm",
                        "User-Agent": "benma-speech-synthesis/1.0",
                    },
                    content=ssml.encode(),
                )
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                "Azure speech synthesis timed out", retryable=True
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(
                "Azure speech synthesis is unavailable", retryable=True
            ) from exc
        if response.status_code >= 400:
            raise ProviderRejectedError(
                f"Azure rejected speech synthesis with HTTP {response.status_code}",
                retryable=response.status_code >= 500,
            )
        if not response.content.startswith(b"RIFF"):
            raise ProviderMalformedResponseError(
                "Azure speech synthesis did not return PCM WAV"
            )
        return SpeechSynthesisResponse(
            audio=response.content,
            mime_type="audio/wav",
            provider_version=request.model_version,
            evidence_status="live_provider",
        )


class DisabledSpeechSynthesisProvider:
    provider_name = "disabled"
    product_name = "speech_synthesis"
    adapter_version = "1.0.0"

    def synthesize(self, request: SpeechSynthesisRequest) -> SpeechSynthesisResponse:
        del request
        raise AnalysisUnsupportedError("speech synthesis is not configured")

"""OpenAI unknown-target transcription adapter with prompt structurally omitted."""

from __future__ import annotations

from typing import Any

import httpx

from benma_api.errors import (
    ProviderMalformedResponseError,
    ProviderRejectedError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from benma_api.speech.contracts import (
    PerceptionEvidence,
    PerceptionProviderResponse,
    UnknownTargetPerceptionInput,
)


def openai_form_fields(model: str, language_hint: str) -> dict[str, str | list[str]]:
    """The complete live request metadata, intentionally incapable of carrying a target."""
    return {
        "model": model,
        "language": language_hint,
        "response_format": "json",
        "include[]": ["logprobs"],
    }


class OpenAITranscriptionProvider:
    provider_name = "openai"
    adapter_version = "1.0.0"

    def __init__(self, api_key: str, model: str = "gpt-4o-transcribe") -> None:
        self.api_key = api_key
        self.product_name = model

    def perceive(self, request: UnknownTargetPerceptionInput) -> PerceptionProviderResponse:
        try:
            response = httpx.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                data=openai_form_fields(self.product_name, request.language_hint),
                files={"file": ("canonical.wav", request.canonical_audio, request.mime_type)},
                timeout=request.timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError("OpenAI transcription timed out", retryable=True) from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(
                "OpenAI transcription is unavailable", retryable=True
            ) from exc
        if response.status_code >= 400:
            raise ProviderRejectedError(
                f"OpenAI rejected transcription with HTTP {response.status_code}",
                retryable=response.status_code >= 500,
            )
        try:
            raw: Any = response.json()
        except ValueError as exc:
            raise ProviderMalformedResponseError("OpenAI returned non-JSON evidence") from exc
        if not isinstance(raw, dict) or not isinstance(raw.get("text"), str):
            raise ProviderMalformedResponseError("OpenAI response has no transcript")
        logprobs = raw.get("logprobs")
        tokens = logprobs if isinstance(logprobs, list) else None
        return PerceptionProviderResponse(
            evidence=PerceptionEvidence(
                transcript=raw["text"],
                alternatives=None,
                tokens=tokens,
                segments=None,
                provider_uncertainty={"logprobs": logprobs} if logprobs is not None else None,
                detected_language=(
                    raw.get("language") if isinstance(raw.get("language"), str) else None
                ),
                evidence_status="live_provider",
            ),
            raw_payload=raw,
        )

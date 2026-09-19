"""Unknown-target transcription with a fixed, nonsemantic server-owned profile."""

from __future__ import annotations

from typing import Any, Literal

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

TranscriptionProfile = Literal["mandarin-verbatim-v1", "language-hint-v0"]
MANDARIN_POLICY = (
    "录音语言是普通话。请用简体汉字逐字转写实际听到的语音。"
    "只转写，不翻译，不纠正语法，不润色，不补全未说完的句子。"  # noqa: RUF001
    "保留犹豫、重复、不寻常的用词和不完整的片段。"
    "不要根据可能的意思纠正发音造成的歧义。"
)


def openai_form_fields(
    model: str, language_hint: str, profile: TranscriptionProfile = "mandarin-verbatim-v1"
) -> dict[str, str | list[str]]:
    """No utterance words, history, target, correction, or arbitrary prompt can enter here."""
    if language_hint != "zh":
        raise ValueError("Mandarin transcription requires the zh language hint")
    if profile not in {"mandarin-verbatim-v1", "language-hint-v0"}:
        raise ValueError("unknown server transcription profile")
    fields: dict[str, str | list[str]] = {
        "model": model,
        "response_format": "json",
    }
    if model == "gpt-transcribe":
        fields["languages[]"] = ["zh"]
    else:
        fields["language"] = "zh"
    if model in {
        "gpt-4o-transcribe",
        "gpt-4o-mini-transcribe",
        "gpt-4o-mini-transcribe-2025-12-15",
    }:
        fields["include[]"] = ["logprobs"]
    if profile == "mandarin-verbatim-v1":
        fields["prompt"] = MANDARIN_POLICY
    return fields


def language_metadata(raw: dict[str, Any]) -> tuple[str | None, list[dict[str, Any]] | None]:
    """Preserve provider declarations, including an explicitly empty languages list."""
    languages = raw.get("languages")
    detected = (
        [item for item in languages if isinstance(item, dict) and isinstance(item.get("code"), str)]
        if isinstance(languages, list)
        else None
    )
    singular = raw.get("language")
    if not isinstance(singular, str) or not singular:
        singular = detected[0]["code"] if detected and len(detected) == 1 else None
    return singular, detected


class OpenAITranscriptionProvider:
    provider_name = "openai"
    adapter_version = "2.0.0"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-transcribe",
        *,
        profile: TranscriptionProfile = "mandarin-verbatim-v1",
    ) -> None:
        self.api_key = api_key
        self.product_name = model
        self.profile = profile
        self.request_configuration = {
            "profile": profile,
            "semantic_hints_supplied": False,
            "output_script": "Hans" if profile == "mandarin-verbatim-v1" else None,
            "form_fields": openai_form_fields(model, "zh", profile),
        }

    def perceive(self, request: UnknownTargetPerceptionInput) -> PerceptionProviderResponse:
        try:
            response = httpx.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                data=openai_form_fields(self.product_name, request.language_hint, self.profile),
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
        detected_language, detected_languages = language_metadata(raw)
        return PerceptionProviderResponse(
            evidence=PerceptionEvidence(
                transcript=raw["text"],
                alternatives=None,
                tokens=tokens,
                segments=None,
                provider_uncertainty={"logprobs": logprobs} if logprobs is not None else None,
                detected_language=detected_language,
                detected_languages=detected_languages,
                evidence_status="live_provider",
            ),
            raw_payload=raw,
        )

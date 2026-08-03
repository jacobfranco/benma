"""OpenAI Transcription API adapter with prompt/context deliberately omitted."""

from __future__ import annotations

import os
from pathlib import Path
from typing import cast

from benchmark.models import UnknownTargetPerceptionRequest, UnknownTargetPerceptionResult
from benchmark.providers.base import (
    MalformedProviderResponseError,
    MissingCredentialsError,
    UnknownTargetPerceptionProvider,
)
from benchmark.providers.http import multipart_request


class OpenAITranscriptionAdapter(UnknownTargetPerceptionProvider):
    provider_name = "openai"
    adapter_version = "1.0.0"

    def __init__(self, model: str = "gpt-4o-transcribe") -> None:
        self.product_name = model

    def perceive(
        self, request: UnknownTargetPerceptionRequest
    ) -> tuple[UnknownTargetPerceptionResult, object]:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise MissingCredentialsError("OPENAI_API_KEY is required")
        raw = multipart_request(
            "https://api.openai.com/v1/audio/transcriptions",
            fields={
                "model": self.product_name,
                "language": "zh",
                "response_format": "json",
                "include[]": "logprobs",
            },
            file_field="file",
            file_path=Path(request.audio.asset_path),
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=request.timeout_seconds,
        )
        if not isinstance(raw, dict) or not isinstance(raw.get("text"), str):
            raise MalformedProviderResponseError("OpenAI response has no text string")
        uncertainty: dict[str, object] = {}
        if "logprobs" in raw:
            uncertainty["logprobs"] = raw["logprobs"]
        result = UnknownTargetPerceptionResult(
            transcript=cast(str, raw["text"]),
            uncertainty=cast(object, uncertainty) if uncertainty else None,
            detected_language=cast(str | None, raw.get("language")),
        )
        return result, raw

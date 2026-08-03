"""Credential-free replay providers used by CI and report fixtures."""

from __future__ import annotations

from copy import deepcopy
from typing import cast

from benchmark.models import (
    KnownTargetAssessmentRequest,
    KnownTargetAssessmentResult,
    UnknownTargetPerceptionRequest,
    UnknownTargetPerceptionResult,
)
from benchmark.providers.base import (
    KnownTargetPronunciationProvider,
    MalformedProviderResponseError,
    UnknownTargetPerceptionProvider,
)


class ReplayUnknownTargetProvider(UnknownTargetPerceptionProvider):
    adapter_version = "1.0.0"

    def __init__(self, provider: str, product: str, responses: dict[str, object]) -> None:
        self.provider_name = provider
        self.product_name = product
        self.responses = responses

    def perceive(
        self, request: UnknownTargetPerceptionRequest
    ) -> tuple[UnknownTargetPerceptionResult, object]:
        if request.sample_id not in self.responses:
            raise MalformedProviderResponseError(f"no replay response for {request.sample_id}")
        raw = deepcopy(self.responses[request.sample_id])
        if not isinstance(raw, dict) or not isinstance(raw.get("text"), str):
            raise MalformedProviderResponseError("replay response has no text string")
        confidence_raw = raw.get("confidence")
        confidence = float(confidence_raw) if isinstance(confidence_raw, int | float) else None
        return (
            UnknownTargetPerceptionResult(
                transcript=cast(str, raw["text"]),
                confidence=confidence,
                detected_language=cast(str | None, raw.get("language")),
            ),
            raw,
        )


class ReplayKnownTargetProvider(KnownTargetPronunciationProvider):
    adapter_version = "1.0.0"

    def __init__(self, provider: str, product: str, responses: dict[str, object]) -> None:
        self.provider_name = provider
        self.product_name = product
        self.responses = responses

    def assess(
        self, request: KnownTargetAssessmentRequest
    ) -> tuple[KnownTargetAssessmentResult, object]:
        if request.sample_id not in self.responses:
            raise MalformedProviderResponseError(f"no replay response for {request.sample_id}")
        raw = deepcopy(self.responses[request.sample_id])
        if not isinstance(raw, dict) or not isinstance(raw.get("normalized"), dict):
            raise MalformedProviderResponseError("known-target replay has no normalized object")
        return KnownTargetAssessmentResult.model_validate(raw["normalized"]), raw

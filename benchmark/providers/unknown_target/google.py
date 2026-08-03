"""Google Cloud Speech-to-Text V2 / Chirp 3 adapter."""

from __future__ import annotations

import base64
import os
from typing import cast

from benchmark.models import (
    TranscriptAlternative,
    UnknownTargetPerceptionRequest,
    UnknownTargetPerceptionResult,
)
from benchmark.providers.base import (
    MalformedProviderResponseError,
    MissingCredentialsError,
    UnknownTargetPerceptionProvider,
)
from benchmark.providers.http import json_request


class GoogleChirpAdapter(UnknownTargetPerceptionProvider):
    provider_name = "google_cloud"
    product_name = "chirp_3"
    adapter_version = "1.0.0"

    def perceive(
        self, request: UnknownTargetPerceptionRequest
    ) -> tuple[UnknownTargetPerceptionResult, object]:
        token = os.environ.get("GOOGLE_CLOUD_ACCESS_TOKEN")
        project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us")
        if not token or not project:
            raise MissingCredentialsError(
                "GOOGLE_CLOUD_ACCESS_TOKEN and GOOGLE_CLOUD_PROJECT are required"
            )
        url = (
            f"https://speech.googleapis.com/v2/projects/{project}/locations/{location}/"
            "recognizers/_:recognize"
        )
        raw = json_request(
            url,
            payload={
                "config": {
                    "autoDecodingConfig": {},
                    "languageCodes": ["cmn-Hans-CN"],
                    "model": self.product_name,
                    "features": {"enableWordTimeOffsets": True, "maxAlternatives": 5},
                },
                "content": base64.b64encode(request.audio.asset_path.read_bytes()).decode(),
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=request.timeout_seconds,
        )
        if not isinstance(raw, dict) or not isinstance(raw.get("results"), list):
            raise MalformedProviderResponseError("Google response has no results list")
        candidates: list[TranscriptAlternative] = []
        primary_parts: list[str] = []
        for item in cast(list[object], raw["results"]):
            if not isinstance(item, dict) or not isinstance(item.get("alternatives"), list):
                continue
            alternatives = cast(list[object], item["alternatives"])
            for index, alternative in enumerate(alternatives):
                if not isinstance(alternative, dict) or not isinstance(
                    alternative.get("transcript"), str
                ):
                    continue
                confidence_raw = alternative.get("confidence")
                confidence = (
                    float(confidence_raw) if isinstance(confidence_raw, int | float) else None
                )
                text = cast(str, alternative["transcript"])
                candidates.append(TranscriptAlternative(transcript=text, confidence=confidence))
                if index == 0:
                    primary_parts.append(text)
        return (
            UnknownTargetPerceptionResult(
                transcript="".join(primary_parts),
                alternatives=tuple(candidates),
                detected_language="cmn-Hans-CN",
            ),
            raw,
        )

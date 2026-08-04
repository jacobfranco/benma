"""Azure known-target pronunciation adapter scoped to Mandarin PCM16 WAV."""

from __future__ import annotations

import base64
import json
from typing import Any

import httpx

from benma_api.errors import (
    ProviderMalformedResponseError,
    ProviderRejectedError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from benma_api.speech.contracts import (
    AssessmentEvidence,
    AssessmentProviderResponse,
    KnownTargetAssessmentInput,
)


class AzurePronunciationProvider:
    provider_name = "azure_speech"
    product_name = "pronunciation_assessment_zh-CN"
    adapter_version = "1.0.0"

    def __init__(self, key: str, region: str) -> None:
        self.key = key
        self.region = region

    def assess(self, request: KnownTargetAssessmentInput) -> AssessmentProviderResponse:
        target = str(request.target_snapshot["text"])
        config = {
            "ReferenceText": target,
            "GradingSystem": "HundredMark",
            "Granularity": "Phoneme",
            "Dimension": "Comprehensive",
            "EnableMiscue": True,
            "PhonemeAlphabet": "SAPI",
        }
        encoded = base64.b64encode(
            json.dumps(config, ensure_ascii=False, separators=(",", ":")).encode()
        ).decode()
        url = (
            f"https://{self.region}.stt.speech.microsoft.com/speech/recognition/"
            "conversation/cognitiveservices/v1?language=zh-CN&format=detailed"
        )
        try:
            response = httpx.post(
                url,
                headers={
                    "Ocp-Apim-Subscription-Key": self.key,
                    "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
                    "Pronunciation-Assessment": encoded,
                    "Accept": "application/json",
                },
                content=request.canonical_audio,
                timeout=request.timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError("Azure assessment timed out", retryable=True) from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(
                "Azure assessment is unavailable", retryable=True
            ) from exc
        if response.status_code >= 400:
            raise ProviderRejectedError(
                f"Azure rejected assessment with HTTP {response.status_code}",
                retryable=response.status_code >= 500,
            )
        try:
            raw: Any = response.json()
            best = raw["NBest"][0]
            assessment = best["PronunciationAssessment"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderMalformedResponseError("Azure response has no assessment") from exc

        syllables: list[dict[str, Any]] = []
        for word in best.get("Words", []):
            if not isinstance(word, dict):
                continue
            word_assessment = word.get("PronunciationAssessment", {})
            phones = []
            for phone in word.get("Phonemes", []):
                if isinstance(phone, dict):
                    phone_assessment = phone.get("PronunciationAssessment", {})
                    phones.append(
                        {
                            "phone": phone.get("Phoneme"),
                            "pronunciation_score": phone_assessment.get("AccuracyScore"),
                        }
                    )
            syllables.append(
                {
                    "text": word.get("Word"),
                    "pronunciation_score": word_assessment.get("AccuracyScore"),
                    "provider_errors": [word_assessment.get("ErrorType")]
                    if word_assessment.get("ErrorType")
                    else [],
                    "phones": phones,
                }
            )

        def score(name: str) -> float | None:
            value = assessment.get(name)
            return float(value) if isinstance(value, int | float) else None

        return AssessmentProviderResponse(
            evidence=AssessmentEvidence(
                overall_score=score("PronScore"),
                pronunciation_score=score("AccuracyScore"),
                fluency_score=score("FluencyScore"),
                completeness_score=score("CompletenessScore"),
                syllables=syllables,
                unsupported_capabilities=[
                    "explicit detected lexical tone",
                    "tone score",
                    "Mandarin surface-tone interpretation",
                ],
            ),
            raw_payload=raw,
        )

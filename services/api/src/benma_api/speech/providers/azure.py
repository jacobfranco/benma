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


def request_azure_speech(
    *, audio: bytes, key: str, region: str, config: dict[str, Any], timeout_seconds: float,
) -> dict[str, Any]:
    """Shared transport only. Each caller separately defines its evidence semantics."""
    encoded = base64.b64encode(
        json.dumps(config, ensure_ascii=False, separators=(",", ":")).encode()
    ).decode()
    url = (
        f"https://{region}.stt.speech.microsoft.com/speech/recognition/"
        "conversation/cognitiveservices/v1?language=zh-CN&format=detailed"
    )
    try:
        response = httpx.post(
            url,
            headers={
                "Ocp-Apim-Subscription-Key": key,
                "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
                "Pronunciation-Assessment": encoded,
                "Accept": "application/json",
            },
            content=audio,
            timeout=timeout_seconds,
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
        if not isinstance(raw, dict):
            raise TypeError("response is not an object")
    except (ValueError, TypeError) as exc:
        raise ProviderMalformedResponseError("Azure returned invalid JSON evidence") from exc
    return raw


class AzurePronunciationProvider:
    provider_name = "azure_speech"
    product_name = "pronunciation_assessment_zh-CN"
    adapter_version = "1.0.1"

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
        raw = request_azure_speech(
            audio=request.canonical_audio, key=self.key, region=self.region,
            config=config, timeout_seconds=request.timeout_seconds,
        )
        try:
            best = raw["NBest"][0]
            if not isinstance(best, dict):
                raise TypeError("Azure NBest item is not an object")
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderMalformedResponseError("Azure response has no assessment") from exc

        nested_assessment = best.get("PronunciationAssessment")
        if isinstance(nested_assessment, dict):
            assessment = nested_assessment
        else:
            # Azure's short-audio REST endpoint may flatten pronunciation
            # assessment fields directly onto NBest[0].
            assessment = {
                key: best[key]
                for key in (
                    "PronScore",
                    "AccuracyScore",
                    "FluencyScore",
                    "CompletenessScore",
                )
                if key in best
            }

        if not assessment:
            raise ProviderMalformedResponseError("Azure response has no assessment")

        syllables: list[dict[str, Any]] = []

        def span(item: dict[str, Any]) -> dict[str, float] | None:
            offset = item.get("Offset")
            duration = item.get("Duration")
            if not isinstance(offset, int | float) or not isinstance(duration, int | float):
                return None
            return {
                "start_seconds": float(offset) / 10_000_000,
                "end_seconds": float(offset + duration) / 10_000_000,
            }

        for word in best.get("Words", []):
            if not isinstance(word, dict):
                continue
            nested_word_assessment = word.get("PronunciationAssessment")
            if isinstance(nested_word_assessment, dict):
                word_assessment = nested_word_assessment
            else:
                word_assessment = {
                    key: word[key]
                    for key in ("AccuracyScore", "ErrorType")
                    if key in word
                }
            phones = []
            for phone in word.get("Phonemes", []):
                if isinstance(phone, dict):
                    nested_phone_assessment = phone.get("PronunciationAssessment")
                    if isinstance(nested_phone_assessment, dict):
                        phone_assessment = nested_phone_assessment
                    else:
                        phone_assessment = {
                            key: phone[key]
                            for key in ("AccuracyScore",)
                            if key in phone
                        }
                    phones.append(
                        {
                            "phone": phone.get("Phoneme"),
                            "pronunciation_score": phone_assessment.get("AccuracyScore"),
                            "timing": span(phone),
                            "provider_assessment": phone_assessment,
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
                    "timing": span(word),
                    "provider_assessment": word_assessment,
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

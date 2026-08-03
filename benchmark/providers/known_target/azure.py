"""Azure Speech Pronunciation Assessment REST adapter for zh-CN."""

from __future__ import annotations

import base64
import json
import os
from typing import cast
from urllib.parse import urlencode

from benchmark.models import (
    KnownTargetAssessmentRequest,
    KnownTargetAssessmentResult,
    PhoneAssessment,
    SyllableAssessment,
)
from benchmark.providers.base import (
    KnownTargetPronunciationProvider,
    MalformedProviderResponseError,
    MissingCredentialsError,
    UnsupportedConfigurationError,
)
from benchmark.providers.http import binary_request


class AzurePronunciationAdapter(KnownTargetPronunciationProvider):
    provider_name = "azure_speech"
    product_name = "pronunciation_assessment_zh-CN"
    adapter_version = "1.0.0"

    def assess(
        self, request: KnownTargetAssessmentRequest
    ) -> tuple[KnownTargetAssessmentResult, object]:
        if request.locale != "zh-CN":
            raise UnsupportedConfigurationError(
                "this adapter is intentionally scoped to Mandarin zh-CN"
            )
        key = os.environ.get("AZURE_SPEECH_KEY")
        region = os.environ.get("AZURE_SPEECH_REGION")
        if not key or not region:
            raise MissingCredentialsError("AZURE_SPEECH_KEY and AZURE_SPEECH_REGION are required")
        config = {
            "ReferenceText": request.target_text,
            "GradingSystem": "HundredMark",
            "Granularity": "Phoneme",
            "Dimension": "Comprehensive",
            "EnableMiscue": True,
            "PhonemeAlphabet": "SAPI",
        }
        encoded_config = base64.b64encode(
            json.dumps(config, ensure_ascii=False, separators=(",", ":")).encode()
        ).decode()
        query = urlencode({"language": request.locale, "format": "detailed"})
        url = (
            f"https://{region}.stt.speech.microsoft.com/speech/recognition/"
            f"conversation/cognitiveservices/v1?{query}"
        )
        raw = binary_request(
            url,
            payload=request.audio.asset_path.read_bytes(),
            headers={
                "Ocp-Apim-Subscription-Key": key,
                "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
                "Pronunciation-Assessment": encoded_config,
                "Accept": "application/json;text/xml",
            },
            timeout=request.timeout_seconds,
        )
        if not isinstance(raw, dict) or not isinstance(raw.get("NBest"), list) or not raw["NBest"]:
            raise MalformedProviderResponseError("Azure response has no NBest result")
        best = cast(dict[str, object], cast(list[object], raw["NBest"])[0])
        assessment = best.get("PronunciationAssessment")
        if not isinstance(assessment, dict):
            raise MalformedProviderResponseError("Azure response has no PronunciationAssessment")
        syllables: list[SyllableAssessment] = []
        for word in cast(list[object], best.get("Words", [])):
            if not isinstance(word, dict):
                continue
            phones: list[PhoneAssessment] = []
            for phone in cast(list[object], word.get("Phonemes", [])):
                if not isinstance(phone, dict):
                    continue
                pa = phone.get("PronunciationAssessment", {})
                score = pa.get("AccuracyScore") if isinstance(pa, dict) else None
                phones.append(
                    PhoneAssessment(
                        phone=cast(str, phone.get("Phoneme", "")),
                        score=float(score) if isinstance(score, int | float) else None,
                    )
                )
            wa = word.get("PronunciationAssessment", {})
            word_score = wa.get("AccuracyScore") if isinstance(wa, dict) else None
            error_type = wa.get("ErrorType") if isinstance(wa, dict) else None
            syllables.append(
                SyllableAssessment(
                    text=cast(str | None, word.get("Word")),
                    score=float(word_score) if isinstance(word_score, int | float) else None,
                    phones=tuple(phones),
                    error_classifications=(str(error_type),) if error_type else (),
                )
            )
        score = lambda name: (  # noqa: E731 - compact guarded vendor extraction
            float(assessment[name]) if isinstance(assessment.get(name), int | float) else None
        )
        return (
            KnownTargetAssessmentResult(
                overall_score=score("PronScore"),
                pronunciation_score=score("AccuracyScore"),
                fluency_score=score("FluencyScore"),
                completeness_score=score("CompletenessScore"),
                syllables=tuple(syllables),
                unsupported_capabilities=(
                    "Mandarin syllable groups",
                    "Mandarin spoken-phoneme alternatives",
                    "explicit detected lexical tone",
                ),
            ),
            raw,
        )

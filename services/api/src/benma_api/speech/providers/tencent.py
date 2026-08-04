"""Tencent Smart Oral Evaluation-New Age (SOE-N) Mandarin adapter.

This module intentionally targets product 1774's WebSocket API. It contains no
code path for the retiring Basic SOE product (product 884).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
import uuid
from collections.abc import Callable
from typing import Any, Literal, cast
from urllib.parse import urlencode

from websockets.exceptions import ConnectionClosed
from websockets.sync.client import connect

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

TencentMode = Literal["sentence", "pinyin"]
Exchange = Callable[[str, bytes, float], list[dict[str, Any]]]

SOE_N_HOST = "soe.cloud.tencent.com"
SOE_N_PATH_PREFIX = "/soe/api/"
SOE_N_ENDPOINT = f"wss://{SOE_N_HOST}{SOE_N_PATH_PREFIX}"
TONE_COMMAND = "{::cmd{F_TDET=true}}"


def _number(value: object) -> float | None:
    return float(value) if isinstance(value, int | float) else None


def _score_from_ratio(value: object) -> float | None:
    parsed = _number(value)
    if parsed is None or parsed < 0:
        return None
    return parsed * 100 if parsed <= 1 else parsed


def _milliseconds_span(item: dict[str, Any]) -> dict[str, float] | None:
    start = _number(item.get("MemBeginTime", item.get("Mbtm")))
    end = _number(item.get("MemEndTime", item.get("Metm")))
    if start is None or end is None or end < start:
        return None
    return {"start_seconds": start / 1000, "end_seconds": end / 1000}


def _valid_tone(value: object) -> int | None:
    return int(value) if isinstance(value, int | float) and int(value) in {0, 1, 2, 3, 4} else None


def parse_tencent_result(raw_result: object) -> AssessmentEvidence:
    """Normalize useful SOE-N detail while treating invalid tone data as absent."""
    if isinstance(raw_result, str):
        try:
            raw_result = json.loads(raw_result)
        except json.JSONDecodeError as exc:
            raise ProviderMalformedResponseError("Tencent SOE-N result is not valid JSON") from exc
    if not isinstance(raw_result, dict):
        raise ProviderMalformedResponseError("Tencent SOE-N result is not an object")
    result = cast(dict[str, Any], raw_result)
    raw_words = result.get("Words", result.get("SentenceInfoSet", {}).get("Words", []))
    if raw_words is None:
        raw_words = []
    if not isinstance(raw_words, list):
        raise ProviderMalformedResponseError("Tencent SOE-N Words is not a list")

    syllables: list[dict[str, Any]] = []
    for raw_word in raw_words:
        if not isinstance(raw_word, dict):
            continue
        word = cast(dict[str, Any], raw_word)
        raw_phones = word.get("PhoneInfos", word.get("PhoneInfo", [])) or []
        phones: list[dict[str, Any]] = []
        if isinstance(raw_phones, list):
            for raw_phone in raw_phones:
                if not isinstance(raw_phone, dict):
                    continue
                phone = cast(dict[str, Any], raw_phone)
                phones.append(
                    {
                        "phone": phone.get("Phone"),
                        "reference_phone": phone.get("ReferencePhone"),
                        "pronunciation_score": _number(phone.get("PronAccuracy")),
                        "match_tag": phone.get("MatchTag"),
                        "reference_letter": phone.get("ReferenceLetter"),
                        "timing": _milliseconds_span(phone),
                        "provider_phone": phone,
                    }
                )
        tone = word.get("Tone")
        tone_data = cast(dict[str, Any], tone) if isinstance(tone, dict) else {}
        tone_valid = tone_data.get("Valid") is True
        reference_tone = _valid_tone(tone_data.get("RefTone")) if tone_valid else None
        detected_tone = (
            _valid_tone(tone_data.get("HypothesisTone", tone_data.get("HypTone")))
            if tone_valid
            else None
        )
        normalized: dict[str, Any] = {
            "text": word.get("Word"),
            "reference_word": word.get("ReferenceWord"),
            "pronunciation_score": _number(word.get("PronAccuracy")),
            "fluency_score": _score_from_ratio(word.get("PronFluency")),
            "match_tag": word.get("MatchTag", word.get("Tag")),
            "phones": phones,
            "timing": _milliseconds_span(word),
            "tone_valid": tone_valid,
            "provider_tone": tone,
            "provider_word": word,
        }
        if reference_tone is not None:
            normalized["reference_tone"] = reference_tone
        if detected_tone is not None:
            normalized["detected_tone"] = detected_tone
        syllables.append(normalized)

    return AssessmentEvidence(
        overall_score=_number(result.get("SuggestedScore")),
        pronunciation_score=_number(result.get("PronAccuracy")),
        fluency_score=_score_from_ratio(result.get("PronFluency")),
        completeness_score=_score_from_ratio(result.get("PronCompletion")),
        syllables=syllables,
        unsupported_capabilities=(
            ["valid explicit tone hypothesis"]
            if syllables and all(not item["tone_valid"] for item in syllables)
            else None
        ),
    )


def _live_exchange(url: str, audio: bytes, timeout_seconds: float) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    try:
        with connect(
            url,
            open_timeout=timeout_seconds,
            close_timeout=min(timeout_seconds, 10),
            max_size=8 * 1024 * 1024,
        ) as websocket:
            handshake = websocket.recv(timeout=timeout_seconds)
            if not isinstance(handshake, str):
                raise ProviderMalformedResponseError("Tencent SOE-N handshake was not text")
            parsed = json.loads(handshake)
            if not isinstance(parsed, dict):
                raise ProviderMalformedResponseError("Tencent SOE-N handshake was not an object")
            messages.append(parsed)
            if parsed.get("code") != 0:
                raise ProviderRejectedError(
                    f"Tencent SOE-N rejected handshake with code {parsed.get('code')}"
                )
            websocket.send(audio)
            websocket.send(json.dumps({"type": "end"}))
            while True:
                response = websocket.recv(timeout=timeout_seconds)
                if not isinstance(response, str):
                    continue
                message = json.loads(response)
                if not isinstance(message, dict):
                    raise ProviderMalformedResponseError("Tencent SOE-N message was not an object")
                messages.append(message)
                code = message.get("code")
                if code != 0:
                    retryable = isinstance(code, int) and code >= 5000
                    raise ProviderRejectedError(
                        f"Tencent SOE-N rejected assessment with code {code}",
                        retryable=retryable,
                    )
                if message.get("final") == 1:
                    return messages
    except TimeoutError as exc:
        raise ProviderTimeoutError("Tencent SOE-N assessment timed out", retryable=True) from exc
    except (OSError, ConnectionClosed) as exc:
        raise ProviderUnavailableError(
            "Tencent SOE-N WebSocket is unavailable", retryable=True
        ) from exc
    except json.JSONDecodeError as exc:
        raise ProviderMalformedResponseError("Tencent SOE-N returned malformed JSON") from exc


class TencentSoenPronunciationProvider:
    """SOE-N sentence or pinyin mode; mode is part of the provider identity."""

    provider_name = "tencent_soe_n"
    adapter_version = "1.0.0"

    def __init__(
        self,
        secret_id: str,
        secret_key: str,
        app_id: str,
        *,
        mode: TencentMode,
        score_coeff: float = 4.0,
        configured_timeout_seconds: float = 30.0,
        exchange: Exchange = _live_exchange,
    ) -> None:
        if not 1.0 <= score_coeff <= 4.0:
            raise ValueError("score_coeff must be in [1.0, 4.0]")
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.app_id = app_id
        self.mode = mode
        self.score_coeff = score_coeff
        self.configured_timeout_seconds = configured_timeout_seconds
        self.exchange = exchange
        self.product_name = f"soe-n_mandarin_{mode}_tone_detection"

    def _reference_text(self, request: KnownTargetAssessmentInput) -> str:
        if self.mode == "sentence":
            target = str(request.target_snapshot.get("text", "")).strip()
        else:
            pinyin = request.target_snapshot.get("pinyin_syllables")
            if not isinstance(pinyin, list) or not pinyin:
                raise ProviderRejectedError("Tencent pinyin mode requires numeric pinyin syllables")
            target = " ".join(str(item) for item in pinyin)
        if not target:
            raise ProviderRejectedError("Tencent SOE-N requires a target")
        return f"{TONE_COMMAND}{target}"

    def _parameters(
        self, request: KnownTargetAssessmentInput, *, now: int, nonce: int, voice_id: str
    ) -> dict[str, str]:
        return {
            "eval_mode": "1" if self.mode == "sentence" else "8",
            "expired": str(now + 300),
            "nonce": str(nonce),
            "rec_mode": "1",
            "ref_text": self._reference_text(request),
            "score_coeff": f"{self.score_coeff:.1f}",
            "secretid": self.secret_id,
            "sentence_info_enabled": "1",
            "server_engine_type": "16k_zh",
            "text_mode": "0",
            "timestamp": str(now),
            "voice_format": "1",
            "voice_id": voice_id,
        }

    def signed_url(
        self,
        request: KnownTargetAssessmentInput,
        *,
        now: int | None = None,
        nonce: int | None = None,
        voice_id: str | None = None,
    ) -> str:
        timestamp = now if now is not None else int(time.time())
        request_nonce = nonce if nonce is not None else secrets.randbelow(2_000_000_000) + 1
        request_voice_id = voice_id or str(uuid.uuid4())
        params = self._parameters(
            request, now=timestamp, nonce=request_nonce, voice_id=request_voice_id
        )
        canonical_query = "&".join(f"{key}={params[key]}" for key in sorted(params))
        signing_text = f"{SOE_N_HOST}{SOE_N_PATH_PREFIX}{self.app_id}?{canonical_query}"
        digest = hmac.new(
            self.secret_key.encode(), signing_text.encode(), hashlib.sha1
        ).digest()
        signature = base64.b64encode(digest).decode()
        return f"{SOE_N_ENDPOINT}{self.app_id}?{urlencode({**params, 'signature': signature})}"

    def assess(self, request: KnownTargetAssessmentInput) -> AssessmentProviderResponse:
        timeout = min(request.timeout_seconds, self.configured_timeout_seconds)
        started = time.perf_counter()
        messages = self.exchange(self.signed_url(request), request.canonical_audio, timeout)
        total_ms = round((time.perf_counter() - started) * 1000)
        result: object | None = None
        for message in messages:
            if message.get("result") is not None:
                result = message["result"]
        if result is None:
            raise ProviderMalformedResponseError("Tencent SOE-N returned no assessment result")
        return AssessmentProviderResponse(
            evidence=parse_tencent_result(result),
            raw_payload={"capture_type": "LIVE_PROVIDER_RESPONSE", "messages": messages},
            provider_version="undocumented",
            request_configuration={
                "product": "SOE-N / Smart Oral Evaluation-New Age",
                "product_documentation_id": 1774,
                "endpoint": f"wss://{SOE_N_HOST}{SOE_N_PATH_PREFIX}{{appid}}",
                "eval_mode": 1 if self.mode == "sentence" else 8,
                "mode": self.mode,
                "score_coeff": self.score_coeff,
                "server_engine_type": "16k_zh",
                "text_mode": 0,
                "tone_detection": True,
                "voice_format": "wav_pcm16_16khz_mono",
                "rec_mode": 1,
                "legacy_basic_product": False,
            },
            transport_timings_ms={"total": total_ms},
        )

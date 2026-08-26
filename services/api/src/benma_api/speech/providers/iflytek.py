"""iFlytek current streaming ISE Mandarin full-dimension adapter."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import UTC, datetime
from email.utils import format_datetime
from typing import Any
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

IFLYTEK_HOST = "ise-api-sg.xf-yun.com"
IFLYTEK_PATH = "/v2/ise"
IFLYTEK_ENDPOINT = f"wss://{IFLYTEK_HOST}{IFLYTEK_PATH}"
FULL_DIMENSION_ABILITIES = "syll_phone_err_msg;pitch;multi_dimension"
Exchange = Callable[[str, dict[str, Any], bytes, float], tuple[list[dict[str, Any]], str]]


def _number(value: object) -> float | None:
    try:
        return float(str(value)) if value is not None and str(value) != "" else None
    except (TypeError, ValueError):
        return None


def _integer(value: object) -> int | None:
    try:
        return int(str(value)) if value is not None and str(value) != "" else None
    except (TypeError, ValueError):
        return None


def _position_span(attributes: dict[str, str]) -> dict[str, Any] | None:
    start = _number(attributes.get("beg_pos"))
    end = _number(attributes.get("end_pos"))
    if start is None or end is None or end < start:
        return None
    return {
        "start_seconds": start / 100,
        "end_seconds": end / 100,
        "provider_start_position": start,
        "provider_end_position": end,
        "provider_position_unit": "10ms_documentation_inferred",
    }


def _tone(value: object) -> int | None:
    if not isinstance(value, str):
        return None
    upper = value.upper()
    if upper.startswith("TONE") and upper[4:].isdigit():
        parsed = int(upper[4:])
        return parsed if parsed in {0, 1, 2, 3, 4} else None
    return None


DP_ERRORS = {
    16: "omission",
    32: "insertion",
    64: "repeat",
    128: "substitution",
}


def _dp_errors(value: object) -> list[str]:
    parsed = _integer(value) or 0
    return [label for flag, label in DP_ERRORS.items() if parsed & flag]


def _phone_error(attributes: dict[str, str]) -> list[str]:
    errors = _dp_errors(attributes.get("dp_message"))
    is_final = attributes.get("is_yun") == "1"
    perr = _integer(attributes.get("perr_msg"))
    if not is_final and perr == 1:
        errors.append("initial_error")
    elif is_final and perr == 1:
        errors.append("final_error")
    elif is_final and perr == 2:
        errors.append("tone_error")
    elif is_final and perr == 3:
        errors.append("final_and_tone_error")
    return errors


def parse_iflytek_xml(xml_text: str) -> tuple[AssessmentEvidence, str | None]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ProviderMalformedResponseError("iFlytek ISE returned malformed XML") from exc
    candidates = [node for node in root.iter() if node.tag.startswith("read_")]
    result_node = next(
        (node for node in reversed(candidates) if "total_score" in node.attrib), None
    )
    if result_node is None:
        rejected = next((node.attrib.get("is_rejected") for node in candidates), None)
        suffix = f" (is_rejected={rejected})" if rejected is not None else ""
        raise ProviderMalformedResponseError(f"iFlytek ISE XML has no scored result{suffix}")

    syllables: list[dict[str, Any]] = []
    provider_errors: set[str] = set()
    for word in result_node.iter("word"):
        real_syllables = [
            node
            for node in word.findall("syll")
            if node.attrib.get("rec_node_type") not in {"sil", "fil"}
        ]
        if not real_syllables:
            real_syllables = list(word.findall("syll"))
        for syllable in real_syllables:
            phones: list[dict[str, Any]] = []
            errors = _dp_errors(syllable.attrib.get("dp_message"))
            reference_tone: int | None = None
            for phone in syllable.findall("phone"):
                phone_errors = _phone_error(phone.attrib)
                errors.extend(phone_errors)
                provider_errors.update(phone_errors)
                reference_tone_for_phone = _tone(phone.attrib.get("mono_tone"))
                if (
                    reference_tone_for_phone is not None
                    and phone.attrib.get("is_yun") == "1"
                ):
                    reference_tone = reference_tone_for_phone
                phones.append(
                    {
                        "phone": phone.attrib.get("content"),
                        "is_final": phone.attrib.get("is_yun") == "1",
                        "pronunciation_score": _number(phone.attrib.get("phone_score")),
                        "reference_tone": reference_tone_for_phone,
                        "error_classifications": phone_errors,
                        "error_confidence_level": _integer(
                            phone.attrib.get("perr_level_msg")
                        ),
                        "perr_msg": _integer(phone.attrib.get("perr_msg")),
                        "dp_message": _integer(phone.attrib.get("dp_message")),
                        "timing": _position_span(phone.attrib),
                        "provider_phone": dict(phone.attrib),
                    }
                )
            provider_errors.update(errors)
            normalized: dict[str, Any] = {
                "text": syllable.attrib.get("content", word.attrib.get("content")),
                "pinyin": syllable.attrib.get("symbol", word.attrib.get("symbol")),
                "pronunciation_score": _number(syllable.attrib.get("total_score")),
                "phone_score": _number(syllable.attrib.get("phone_score")),
                "tone_score": _number(syllable.attrib.get("tone_score")),
                "phones": phones,
                "error_classifications": sorted(set(errors)),
                "dp_message": _integer(syllable.attrib.get("dp_message")),
                "timing": _position_span(syllable.attrib),
                "provider_syllable": dict(syllable.attrib),
            }
            if reference_tone is not None:
                normalized["reference_tone"] = reference_tone
            syllables.append(normalized)

    attributes = result_node.attrib
    outer_version = next(
        (node.attrib.get("version") for node in candidates if node.attrib.get("version")), None
    )
    return (
        AssessmentEvidence(
            overall_score=_number(attributes.get("total_score")),
            pronunciation_score=_number(attributes.get("accuracy_score")),
            fluency_score=_number(attributes.get("fluency_score")),
            completeness_score=_number(attributes.get("integrity_score")),
            phone_score=_number(attributes.get("phone_score")),
            tone_score=_number(attributes.get("tone_score")),
            integrity_score=_number(attributes.get("integrity_score")),
            syllables=syllables,
            audio_quality={
                "is_rejected": attributes.get("is_rejected"),
                "except_info": attributes.get("except_info"),
            },
            provider_error_classifications=sorted(provider_errors),
        ),
        outer_version,
    )


def _live_exchange(
    url: str, start_payload: dict[str, Any], audio: bytes, timeout_seconds: float
) -> tuple[list[dict[str, Any]], str]:
    messages: list[dict[str, Any]] = []
    try:
        with connect(
            url,
            open_timeout=timeout_seconds,
            close_timeout=min(timeout_seconds, 10),
            max_size=12 * 1024 * 1024,
        ) as websocket:
            websocket.send(json.dumps(start_payload, ensure_ascii=False))
            chunks = [audio[index : index + 1280] for index in range(0, len(audio), 1280)]
            if not chunks:
                chunks = [b""]
            for index, chunk in enumerate(chunks):
                final = index == len(chunks) - 1
                websocket.send(
                    json.dumps(
                        {
                            "business": {
                                "cmd": "auw",
                                "aus": 4 if final else 1 if index == 0 else 2,
                                "aue": "raw",
                            },
                            "data": {
                                "status": 2 if final else 1,
                                "data": base64.b64encode(chunk).decode(),
                                "data_type": 1,
                                "encoding": "raw",
                            },
                        }
                    )
                )
            while True:
                response = websocket.recv(timeout=timeout_seconds)
                if not isinstance(response, str):
                    continue
                message = json.loads(response)
                if not isinstance(message, dict):
                    raise ProviderMalformedResponseError("iFlytek ISE message is not an object")
                messages.append(message)
                if message.get("code") != 0:
                    raise ProviderRejectedError(
                        f"iFlytek ISE rejected assessment with code {message.get('code')}: "
                        f"{message.get('message')}",
                        retryable=False,
                    )
                data = message.get("data")
                if isinstance(data, dict) and data.get("status") == 2:
                    encoded = data.get("data")
                    if not isinstance(encoded, str):
                        raise ProviderMalformedResponseError(
                            "iFlytek ISE final response has no result data"
                        )
                    try:
                        return messages, base64.b64decode(encoded).decode("utf-8")
                    except (ValueError, UnicodeDecodeError) as exc:
                        raise ProviderMalformedResponseError(
                            "iFlytek ISE result is not valid base64 UTF-8"
                        ) from exc
    except TimeoutError as exc:
        raise ProviderTimeoutError("iFlytek ISE assessment timed out", retryable=True) from exc
    except (OSError, ConnectionClosed) as exc:
        raise ProviderUnavailableError(
            "iFlytek ISE WebSocket is unavailable", retryable=True
        ) from exc
    except json.JSONDecodeError as exc:
        raise ProviderMalformedResponseError("iFlytek ISE returned malformed JSON") from exc


class IflytekIsePronunciationProvider:
    provider_name = "iflytek_ise"
    product_name = "streaming_mandarin_full_dimension"
    adapter_version = "1.0.2"

    def __init__(
        self,
        app_id: str,
        api_key: str,
        api_secret: str,
        *,
        configured_timeout_seconds: float = 45.0,
        exchange: Exchange = _live_exchange,
    ) -> None:
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.configured_timeout_seconds = configured_timeout_seconds
        self.exchange = exchange

    def signed_url(self, *, now: datetime | None = None) -> str:
        current = (now or datetime.now(UTC)).astimezone(UTC)
        date = format_datetime(current, usegmt=True)
        signing_text = f"host: {IFLYTEK_HOST}\ndate: {date}\nGET {IFLYTEK_PATH} HTTP/1.1"
        signature = base64.b64encode(
            hmac.new(
                self.api_secret.encode(), signing_text.encode(), hashlib.sha256
            ).digest()
        ).decode()
        origin = (
            f'api_key="{self.api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature="{signature}"'
        )
        authorization = base64.b64encode(origin.encode()).decode()
        query = urlencode(
            {"authorization": authorization, "host": IFLYTEK_HOST, "date": date}
        )
        return f"{IFLYTEK_ENDPOINT}?{query}"

    def start_payload(self, request: KnownTargetAssessmentInput) -> dict[str, Any]:
        target = str(request.target_snapshot.get("text", "")).strip()
        if not target:
            raise ProviderRejectedError("iFlytek ISE requires a Mandarin target")
        return {
            "common": {"app_id": self.app_id},
            "business": {
                "sub": "ise",
                "ent": "cn_vip",
                "category": "read_sentence",
                "cmd": "ssb",
                "text": f"\ufeff{target}",
                "tte": "utf-8",
                "ttp_skip": True,
                "aue": "raw",
                "auf": "audio/L16;rate=16000",
                "rstcd": "utf8",
                "rst": "entirety",
                "ise_unite": "1",
                "extra_ability": FULL_DIMENSION_ABILITIES,
                "group": "adult",
            },
            "data": {"status": 0, "data": ""},
        }

    def assess(self, request: KnownTargetAssessmentInput) -> AssessmentProviderResponse:
        timeout = min(request.timeout_seconds, self.configured_timeout_seconds)
        start_payload = self.start_payload(request)
        started = time.perf_counter()
        messages, xml_text = self.exchange(
            self.signed_url(), start_payload, request.canonical_audio, timeout
        )
        total_ms = round((time.perf_counter() - started) * 1000)
        evidence, version = parse_iflytek_xml(xml_text)
        sanitized_envelopes: list[dict[str, Any]] = []
        for message in messages:
            copy = dict(message)
            data = copy.get("data")
            if isinstance(data, dict):
                copy["data"] = {key: value for key, value in data.items() if key != "data"}
            sanitized_envelopes.append(copy)
        return AssessmentProviderResponse(
            evidence=evidence,
            raw_payload={
                "capture_type": "LIVE_PROVIDER_RESPONSE",
                "envelopes": sanitized_envelopes,
                "result_xml": xml_text,
            },
            provider_version=version or "undocumented",
            request_configuration={
                "product": "iFlytek Streaming Pronunciation Assessment",
                "endpoint": IFLYTEK_ENDPOINT,
                "sub": "ise",
                "ent": "cn_vip",
                "category": "read_sentence",
                "rst": "entirety",
                "ise_unite": "1",
                "extra_ability": FULL_DIMENSION_ABILITIES,
                "group": "adult",
                "audio": "PCM16_16khz_mono",
                "full_dimension_requested": True,
            },
            transport_timings_ms={"total": total_ms},
        )

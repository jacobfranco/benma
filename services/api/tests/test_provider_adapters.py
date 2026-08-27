from __future__ import annotations

import base64
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from benma_api.config import Settings
from benma_api.errors import (
    AnalysisUnsupportedError,
    ProviderMalformedResponseError,
    ProviderRejectedError,
    ProviderTimeoutError,
)
from benma_api.speech.contracts import (
    KnownTargetAssessmentInput,
    UnknownTargetPerceptionInput,
)
from benma_api.speech.providers.azure import AzurePronunciationProvider
from benma_api.speech.providers.factory import (
    build_assessment_provider,
    build_perception_provider,
)
from benma_api.speech.providers.iflytek import (
    FULL_DIMENSION_ABILITIES,
    IFLYTEK_ENDPOINT,
    IFLYTEK_HOST,
    IFLYTEK_PATH,
    IflytekIsePronunciationProvider,
    parse_iflytek_xml,
)
from benma_api.speech.providers.tencent import (
    SOE_N_ENDPOINT,
    TONE_COMMAND,
    TencentSoenPronunciationProvider,
    parse_tencent_result,
)
from benma_api.speech.raw_evidence import encode_raw_payload


def test_azure_serializes_target_and_preserves_only_supported_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class Response:
        status_code = 200

        def json(self) -> dict[str, object]:
            return {
                "NBest": [
                    {
                        "PronunciationAssessment": {
                            "PronScore": 81.0,
                            "AccuracyScore": 79.0,
                            "FluencyScore": 77.0,
                            "CompletenessScore": 100.0,
                        },
                        "Words": [
                            {
                                "Word": "生活",
                                "PronunciationAssessment": {
                                    "AccuracyScore": 79.0,
                                    "ErrorType": "None",
                                },
                                "Phonemes": [
                                    {
                                        "Phoneme": "sh",
                                        "PronunciationAssessment": {"AccuracyScore": 76.0},
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }

    def fake_post(url: str, **kwargs: object) -> Response:
        captured["url"] = url
        captured.update(kwargs)
        return Response()

    monkeypatch.setattr(httpx, "post", fake_post)
    result = AzurePronunciationProvider("secret-test-key", "eastus").assess(
        KnownTargetAssessmentInput(
            attempt_id=uuid.uuid4(),
            canonical_audio=b"wav",
            mime_type="audio/wav",
            target_snapshot={"text": "生活", "lexical_tones": [1, 2]},
            timeout_seconds=30,
        )
    )

    headers = captured["headers"]
    assert isinstance(headers, dict)
    encoded = headers["Pronunciation-Assessment"]
    assert isinstance(encoded, str)
    request_config = json.loads(base64.b64decode(encoded))
    assert request_config["ReferenceText"] == "生活"
    normalized = result.evidence.normalized()
    assert normalized["overall_score"] == 81.0
    assert normalized["syllables"][0]["phones"][0]["phone"] == "sh"
    assert "detected_tone" not in str(normalized)
    assert "tone score" in normalized["unsupported_capabilities"]


def test_azure_accepts_flattened_short_audio_pronunciation_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Response:
        status_code = 200

        def json(self) -> dict[str, object]:
            return {
                "RecognitionStatus": "Success",
                "DisplayText": "生活。",
                "NBest": [
                    {
                        "AccuracyScore": 95.0,
                        "FluencyScore": 100.0,
                        "CompletenessScore": 100.0,
                        "PronScore": 97.0,
                        "Words": [
                            {
                                "Word": "生活",
                                "Offset": 47_100_000,
                                "Duration": 11_400_000,
                                "AccuracyScore": 95.0,
                                "ErrorType": "None",
                                "Phonemes": [
                                    {
                                        "Phoneme": "sheng 1",
                                        "Offset": 47_100_000,
                                        "Duration": 4_900_000,
                                        "AccuracyScore": 83.0,
                                    },
                                    {
                                        "Phoneme": "huo 2",
                                        "Offset": 52_100_000,
                                        "Duration": 6_400_000,
                                        "AccuracyScore": 96.0,
                                    },
                                ],
                            }
                        ],
                    }
                ],
            }

    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: Response())

    result = AzurePronunciationProvider("secret-test-key", "eastus").assess(
        KnownTargetAssessmentInput(
            attempt_id=uuid.uuid4(),
            canonical_audio=b"wav",
            mime_type="audio/wav",
            target_snapshot={"text": "生活", "lexical_tones": [1, 2]},
            timeout_seconds=30,
        )
    )

    normalized = result.evidence.normalized()

    assert normalized["overall_score"] == 97.0
    assert normalized["pronunciation_score"] == 95.0
    assert normalized["fluency_score"] == 100.0
    assert normalized["completeness_score"] == 100.0

    word = normalized["syllables"][0]
    assert word["text"] == "生活"
    assert word["pronunciation_score"] == 95.0
    assert word["provider_errors"] == ["None"]
    assert word["timing"] == {
        "start_seconds": 4.71,
        "end_seconds": 5.85,
    }

    phones = word["phones"]
    assert phones[0]["phone"] == "sheng 1"
    assert phones[0]["pronunciation_score"] == 83.0
    assert phones[1]["phone"] == "huo 2"
    assert phones[1]["pronunciation_score"] == 96.0

    assert isinstance(result.raw_payload, dict)
    assert result.raw_payload["RecognitionStatus"] == "Success"


def test_provider_registry_is_closed_and_disabled_is_explicit() -> None:
    perception = build_perception_provider(Settings(perception_provider="disabled"))
    with pytest.raises(AnalysisUnsupportedError):
        perception.perceive(
            UnknownTargetPerceptionInput(uuid.uuid4(), b"wav", "audio/wav", "zh", 30)
        )

    assessment = build_assessment_provider(Settings(assessment_provider="disabled"))
    with pytest.raises(AnalysisUnsupportedError):
        assessment.assess(
            KnownTargetAssessmentInput(uuid.uuid4(), b"wav", "audio/wav", {"text": "生活"}, 30)
        )


def test_raw_provider_payload_supports_text_and_non_json_values() -> None:
    text = encode_raw_payload("provider text")
    assert text.json_value is None and text.text_value == "provider text"
    assert len(text.sha256) == 64

    non_json = encode_raw_payload({"value": {1, 2}})
    assert non_json.json_value is None
    assert non_json.text_value is not None
    assert len(non_json.sha256) == 64


def test_tencent_soen_sentence_request_targets_new_age_and_enables_tone() -> None:
    request = KnownTargetAssessmentInput(
        attempt_id=uuid.uuid4(),
        canonical_audio=b"wav",
        mime_type="audio/wav",
        target_snapshot={"text": "生活", "pinyin_syllables": ["sheng1", "huo2"]},
        timeout_seconds=30,
    )
    provider = TencentSoenPronunciationProvider(
        "secret-id", "secret-key", "123456", mode="sentence"
    )
    url = provider.signed_url(request, now=1_700_000_000, nonce=7, voice_id="voice-test")
    assert url.startswith(f"{SOE_N_ENDPOINT}123456?")
    assert "eval_mode=1" in url
    assert "server_engine_type=16k_zh" in url
    assert "F_TDET%3Dtrue" in url
    assert "secret-key" not in url
    assert "/soe/api/" in url
    assert "/soe-b/" not in url


def test_tencent_soen_pinyin_mode_keeps_mode_separate() -> None:
    captured: dict[str, object] = {}

    def exchange(url: str, audio: bytes, timeout: float) -> list[dict[str, object]]:
        captured.update(url=url, audio=audio, timeout=timeout)
        return [
            {"code": 0, "message": "success"},
            {
                "code": 0,
                "result": {
                    "SuggestedScore": 91,
                    "PronAccuracy": 89,
                    "Words": [
                        {
                            "Word": "生",
                            "ReferenceWord": "sheng1",
                            "PronAccuracy": 88,
                            "Tone": {"Valid": True, "RefTone": 1, "HypothesisTone": 2},
                            "PhoneInfos": [],
                        }
                    ],
                },
            },
            {"code": 0, "final": 1},
        ]

    provider = TencentSoenPronunciationProvider(
        "secret-id", "secret-key", "123456", mode="pinyin", exchange=exchange
    )
    result = provider.assess(
        KnownTargetAssessmentInput(
            attempt_id=uuid.uuid4(),
            canonical_audio=b"same-canonical-wav",
            mime_type="audio/wav",
            target_snapshot={"text": "生活", "pinyin_syllables": ["sheng1", "huo2"]},
            timeout_seconds=30,
        )
    )
    assert "eval_mode=8" in str(captured["url"])
    assert "sheng1+huo2" in str(captured["url"])
    assert captured["audio"] == b"same-canonical-wav"
    assert result.request_configuration is not None
    assert result.request_configuration["mode"] == "pinyin"
    assert result.evidence.syllables is not None
    assert result.evidence.syllables[0]["detected_tone"] == 2


def test_tencent_invalid_tone_is_missing_not_negative_one() -> None:
    evidence = parse_tencent_result(
        {
            "SuggestedScore": 99,
            "Words": [
                {
                    "Word": "清",
                    "ReferenceWord": "qing1",
                    "Tone": {"Valid": False, "RefTone": -1, "HypothesisTone": -1},
                    "PhoneInfos": [
                        {
                            "Phone": "ing1",
                            "ReferencePhone": "ing1",
                            "PronAccuracy": 99,
                            "MemBeginTime": 100,
                            "MemEndTime": 240,
                        }
                    ],
                }
            ],
        }
    )
    assert evidence.syllables is not None
    syllable = evidence.syllables[0]
    assert syllable["tone_valid"] is False
    assert "reference_tone" not in syllable
    assert "detected_tone" not in syllable
    assert "valid explicit tone hypothesis" in (evidence.unsupported_capabilities or [])


def test_tencent_tone_command_is_pinned() -> None:
    assert TONE_COMMAND == "{::cmd{F_TDET=true}}"


def test_tencent_rejects_missing_pinyin_and_malformed_result() -> None:
    provider = TencentSoenPronunciationProvider(
        "secret-id", "secret-key", "123456", mode="pinyin"
    )
    request = KnownTargetAssessmentInput(
        attempt_id=uuid.uuid4(),
        canonical_audio=b"wav",
        mime_type="audio/wav",
        target_snapshot={"text": "生活"},
        timeout_seconds=30,
    )
    with pytest.raises(ProviderRejectedError, match="numeric pinyin"):
        provider.signed_url(request)
    with pytest.raises(ProviderMalformedResponseError, match="valid JSON"):
        parse_tencent_result("not-json")


def test_tencent_timeout_is_not_replayed() -> None:
    def timeout(_url: str, _audio: bytes, _seconds: float):  # type: ignore[no-untyped-def]
        raise ProviderTimeoutError("timed out", retryable=True)

    provider = TencentSoenPronunciationProvider(
        "secret-id", "secret-key", "123456", mode="sentence", exchange=timeout
    )
    request = KnownTargetAssessmentInput(
        attempt_id=uuid.uuid4(),
        canonical_audio=b"wav",
        mime_type="audio/wav",
        target_snapshot={"text": "生活"},
        timeout_seconds=30,
    )
    with pytest.raises(ProviderTimeoutError):
        provider.assess(request)


def test_iflytek_full_dimension_request_and_auth_do_not_expose_secret() -> None:
    provider = IflytekIsePronunciationProvider("app-id", "api-key", "api-secret")
    request = KnownTargetAssessmentInput(
        attempt_id=uuid.uuid4(),
        canonical_audio=b"wav",
        mime_type="audio/wav",
        target_snapshot={"text": "生活"},
        timeout_seconds=30,
    )
    payload = provider.start_payload(request)
    business = payload["business"]
    assert business["ent"] == "cn_vip"
    assert business["ise_unite"] == "1"
    assert business["rst"] == "entirety"
    assert business["extra_ability"] == FULL_DIMENSION_ABILITIES
    assert business["text"] == "\ufeff生活"
    url = provider.signed_url(now=datetime(2026, 8, 3, tzinfo=UTC))
    assert IFLYTEK_HOST == "ise-api-sg.xf-yun.com"
    assert IFLYTEK_PATH == "/v2/ise"
    assert IFLYTEK_ENDPOINT == "wss://ise-api-sg.xf-yun.com/v2/ise"
    assert url.startswith(f"{IFLYTEK_ENDPOINT}?")
    assert "api-secret" not in url
    assert "api-key" not in url


def test_iflytek_fixture_preserves_tone_phone_and_error_structure() -> None:
    fixture = (
        Path(__file__).parent
        / "fixtures"
        / "iflytek-ise"
        / "mandarin-full-dimension.xml"
    ).read_text(encoding="utf-8")
    evidence, version = parse_iflytek_xml(fixture)
    assert version == "7,0,0,1024"
    assert evidence.overall_score == 80
    assert evidence.pronunciation_score == 78
    assert evidence.phone_score == 82
    assert evidence.tone_score == 70
    assert evidence.syllables is not None
    first = evidence.syllables[0]
    assert first["pinyin"] == "sheng1"
    assert first["reference_tone"] == 1
    assert "detected_tone" not in first
    assert "tone_error" in first["error_classifications"]
    second = evidence.syllables[1]
    assert "initial_error" in second["error_classifications"]
    assert second["phones"][0]["error_confidence_level"] == 2


def test_iflytek_zero_accuracy_is_unavailable_when_other_scores_are_populated() -> None:
    xml = """<xml_result><read_sentence version="1">
    <read_sentence accuracy_score="0.000000" total_score="67.4"
      fluency_score="80" integrity_score="100" phone_score="75" tone_score="100">
    </read_sentence></read_sentence></xml_result>"""

    evidence, _ = parse_iflytek_xml(xml)

    assert evidence.overall_score == 67.4
    assert evidence.pronunciation_score is None
    assert evidence.phone_score == 75
    assert evidence.tone_score == 100


def test_iflytek_live_wrapper_keeps_identical_audio_and_sanitizes_envelope() -> None:
    fixture = (
        Path(__file__).parent
        / "fixtures"
        / "iflytek-ise"
        / "mandarin-full-dimension.xml"
    ).read_text(encoding="utf-8")
    captured: dict[str, object] = {}

    def exchange(
        url: str, start: dict[str, object], audio: bytes, timeout: float
    ) -> tuple[list[dict[str, object]], str]:
        captured.update(url=url, start=start, audio=audio, timeout=timeout)
        return ([{"code": 0, "data": {"status": 2, "data": "sensitive-copy"}}], fixture)

    provider = IflytekIsePronunciationProvider(
        "app-id", "api-key", "api-secret", exchange=exchange
    )
    response = provider.assess(
        KnownTargetAssessmentInput(
            attempt_id=uuid.uuid4(),
            canonical_audio=b"same-canonical-audio",
            mime_type="audio/wav",
            target_snapshot={"text": "生活"},
            timeout_seconds=30,
        )
    )
    assert captured["audio"] == b"same-canonical-audio"
    assert response.request_configuration is not None
    assert response.request_configuration["full_dimension_requested"] is True
    assert "sensitive-copy" not in str(response.raw_payload)


def test_iflytek_malformed_xml_and_empty_target_are_rejected() -> None:
    with pytest.raises(ProviderMalformedResponseError, match="malformed XML"):
        parse_iflytek_xml("<not-closed>")
    provider = IflytekIsePronunciationProvider("app-id", "api-key", "api-secret")
    request = KnownTargetAssessmentInput(
        attempt_id=uuid.uuid4(),
        canonical_audio=b"wav",
        mime_type="audio/wav",
        target_snapshot={"text": ""},
        timeout_seconds=30,
    )
    with pytest.raises(ProviderRejectedError, match="requires a Mandarin target"):
        provider.start_payload(request)


def test_iflytek_preserves_dp_omission_and_substitution() -> None:
    xml = """<xml_result><read_sentence version="1"><read_sentence total_score="50">
    <word><syll content="生" symbol="sheng1" dp_message="16">
    <phone content="sh" is_yun="0" dp_message="128" perr_msg="1" perr_level_msg="3"/>
    </syll></word></read_sentence></read_sentence></xml_result>"""
    evidence, _ = parse_iflytek_xml(xml)
    assert evidence.syllables is not None
    classifications = evidence.syllables[0]["error_classifications"]
    assert "omission" in classifications
    assert "substitution" in classifications
    assert "initial_error" in classifications

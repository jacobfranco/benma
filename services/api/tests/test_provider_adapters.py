from __future__ import annotations

import base64
import json
import uuid

import httpx
import pytest

from benma_api.config import Settings
from benma_api.errors import AnalysisUnsupportedError
from benma_api.speech.contracts import (
    KnownTargetAssessmentInput,
    UnknownTargetPerceptionInput,
)
from benma_api.speech.providers.azure import AzurePronunciationProvider
from benma_api.speech.providers.factory import (
    build_assessment_provider,
    build_perception_provider,
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
    assert normalized["syllables"][0]["phones"][0]["phone"] == "sh"  # type: ignore[index]
    assert "detected_tone" not in str(normalized)
    assert "tone score" in normalized["unsupported_capabilities"]  # type: ignore[operator]


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

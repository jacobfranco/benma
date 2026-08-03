from __future__ import annotations

import pytest

from benchmark.models import KnownTargetAssessmentRequest, UnknownTargetPerceptionRequest
from benchmark.providers.base import (
    MalformedProviderResponseError,
    MissingCredentialsError,
    UnsupportedConfigurationError,
)
from benchmark.providers.known_target.azure import AzurePronunciationAdapter
from benchmark.providers.replay import ReplayKnownTargetProvider, ReplayUnknownTargetProvider
from benchmark.providers.unknown_target.google import GoogleChirpAdapter
from benchmark.providers.unknown_target.local import JsonCommandPerceptionAdapter
from benchmark.providers.unknown_target.openai import OpenAITranscriptionAdapter


def test_replay_unknown_success_and_raw_copy(recorded_sample) -> None:  # type: ignore[no-untyped-def]
    raw = {"text": "你好", "confidence": 0.8, "vendor": {"x": 1}}
    provider = ReplayUnknownTargetProvider("fixture", "model", {"test_sample": raw})
    result, returned = provider.perceive(recorded_sample.perception_request())
    assert result.transcript == "你好"
    assert returned == raw
    assert returned is not raw


def test_replay_unknown_missing_sample_is_malformed(recorded_sample) -> None:  # type: ignore[no-untyped-def]
    provider = ReplayUnknownTargetProvider("fixture", "model", {})
    with pytest.raises(MalformedProviderResponseError):
        provider.perceive(recorded_sample.perception_request())


def test_replay_known_rejects_malformed(recorded_sample) -> None:  # type: ignore[no-untyped-def]
    assert recorded_sample.audio
    request = KnownTargetAssessmentRequest(
        sample_id=recorded_sample.sample_id,
        audio=recorded_sample.audio,
        target_text="你好",
    )
    provider = ReplayKnownTargetProvider("fixture", "model", {"test_sample": {"bad": True}})
    with pytest.raises(MalformedProviderResponseError):
        provider.assess(request)


@pytest.mark.parametrize(
    ("adapter", "variables"),
    [
        (OpenAITranscriptionAdapter(), ["OPENAI_API_KEY"]),
        (GoogleChirpAdapter(), ["GOOGLE_CLOUD_ACCESS_TOKEN", "GOOGLE_CLOUD_PROJECT"]),
    ],
)
def test_unknown_live_adapters_report_missing_credentials(
    adapter,
    variables: list[str],
    recorded_sample,
    monkeypatch: pytest.MonkeyPatch,  # type: ignore[no-untyped-def]
) -> None:
    for variable in variables:
        monkeypatch.delenv(variable, raising=False)
    with pytest.raises(MissingCredentialsError):
        adapter.perceive(recorded_sample.perception_request())


def test_azure_reports_missing_credentials(
    recorded_sample, monkeypatch: pytest.MonkeyPatch
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("AZURE_SPEECH_KEY", raising=False)
    monkeypatch.delenv("AZURE_SPEECH_REGION", raising=False)
    assert recorded_sample.audio
    request = KnownTargetAssessmentRequest(
        sample_id=recorded_sample.sample_id,
        audio=recorded_sample.audio,
        target_text="你好",
    )
    with pytest.raises(MissingCredentialsError):
        AzurePronunciationAdapter().assess(request)


def test_openai_adapter_never_sends_prompt(
    recorded_sample,
    monkeypatch: pytest.MonkeyPatch,  # type: ignore[no-untyped-def]
) -> None:
    captured: dict[str, object] = {}

    def fake_request(url: str, **kwargs: object) -> object:
        captured.update(kwargs)
        return {"text": "你好", "logprobs": [{"token": "你"}]}

    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    monkeypatch.setattr("benchmark.providers.unknown_target.openai.multipart_request", fake_request)
    result, _ = OpenAITranscriptionAdapter().perceive(recorded_sample.perception_request())
    assert result.transcript == "你好"
    fields = captured["fields"]
    assert isinstance(fields, dict)
    assert "prompt" not in fields
    assert "context" not in fields


def test_openai_adapter_rejects_malformed_response(
    recorded_sample,
    monkeypatch: pytest.MonkeyPatch,  # type: ignore[no-untyped-def]
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    monkeypatch.setattr(
        "benchmark.providers.unknown_target.openai.multipart_request",
        lambda *args, **kwargs: {"unexpected": True},
    )
    with pytest.raises(MalformedProviderResponseError):
        OpenAITranscriptionAdapter().perceive(recorded_sample.perception_request())


def test_google_adapter_never_sends_prompt(
    recorded_sample,
    monkeypatch: pytest.MonkeyPatch,  # type: ignore[no-untyped-def]
) -> None:
    captured: dict[str, object] = {}

    def fake_request(url: str, **kwargs: object) -> object:
        captured.update(kwargs)
        return {"results": [{"alternatives": [{"transcript": "你好", "confidence": 0.8}]}]}

    monkeypatch.setenv("GOOGLE_CLOUD_ACCESS_TOKEN", "test-only")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setattr("benchmark.providers.unknown_target.google.json_request", fake_request)
    result, _ = GoogleChirpAdapter().perceive(recorded_sample.perception_request())
    assert result.transcript == "你好"
    payload = captured["payload"]
    assert isinstance(payload, dict)
    serialized = str(payload).lower()
    assert "prompt" not in serialized
    assert "phrase" not in serialized


def test_google_adapter_rejects_malformed_response(
    recorded_sample,
    monkeypatch: pytest.MonkeyPatch,  # type: ignore[no-untyped-def]
) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_ACCESS_TOKEN", "test-only")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setattr(
        "benchmark.providers.unknown_target.google.json_request",
        lambda *args, **kwargs: {"unexpected": True},
    )
    with pytest.raises(MalformedProviderResponseError):
        GoogleChirpAdapter().perceive(recorded_sample.perception_request())


def test_azure_normalizes_documented_scores(
    recorded_sample,
    monkeypatch: pytest.MonkeyPatch,  # type: ignore[no-untyped-def]
) -> None:
    raw = {
        "NBest": [
            {
                "PronunciationAssessment": {
                    "PronScore": 88,
                    "AccuracyScore": 86,
                    "FluencyScore": 90,
                    "CompletenessScore": 100,
                },
                "Words": [
                    {
                        "Word": "你",
                        "PronunciationAssessment": {"AccuracyScore": 82, "ErrorType": "None"},
                        "Phonemes": [
                            {"Phoneme": "n", "PronunciationAssessment": {"AccuracyScore": 80}}
                        ],
                    }
                ],
            }
        ]
    }
    monkeypatch.setenv("AZURE_SPEECH_KEY", "test-only")
    monkeypatch.setenv("AZURE_SPEECH_REGION", "eastus")
    monkeypatch.setattr(
        "benchmark.providers.known_target.azure.binary_request", lambda *a, **k: raw
    )
    assert recorded_sample.audio
    result, returned = AzurePronunciationAdapter().assess(
        KnownTargetAssessmentRequest(
            sample_id=recorded_sample.sample_id,
            audio=recorded_sample.audio,
            target_text="你好",
        )
    )
    assert result.overall_score == 88
    assert result.syllables[0].phones[0].phone == "n"
    assert "explicit detected lexical tone" in result.unsupported_capabilities
    assert returned is raw


def test_azure_rejects_unsupported_locale(recorded_sample) -> None:  # type: ignore[no-untyped-def]
    assert recorded_sample.audio
    request = KnownTargetAssessmentRequest(
        sample_id=recorded_sample.sample_id,
        audio=recorded_sample.audio,
        target_text="你好",
        locale="en-US",
    )
    with pytest.raises(UnsupportedConfigurationError, match="zh-CN"):
        AzurePronunciationAdapter().assess(request)


def test_azure_rejects_malformed_response(
    recorded_sample,
    monkeypatch: pytest.MonkeyPatch,  # type: ignore[no-untyped-def]
) -> None:
    monkeypatch.setenv("AZURE_SPEECH_KEY", "test-only")
    monkeypatch.setenv("AZURE_SPEECH_REGION", "eastus")
    monkeypatch.setattr(
        "benchmark.providers.known_target.azure.binary_request",
        lambda *args, **kwargs: {"unexpected": True},
    )
    assert recorded_sample.audio
    request = KnownTargetAssessmentRequest(
        sample_id=recorded_sample.sample_id,
        audio=recorded_sample.audio,
        target_text="你好",
    )
    with pytest.raises(MalformedProviderResponseError):
        AzurePronunciationAdapter().assess(request)


def test_local_adapter_reports_missing_executable(recorded_sample) -> None:  # type: ignore[no-untyped-def]
    provider = JsonCommandPerceptionAdapter(
        "local", "missing", ("definitely-not-a-benma-executable", "{audio}")
    )
    with pytest.raises(UnsupportedConfigurationError, match="not found"):
        provider.perceive(recorded_sample.perception_request())


def test_unknown_request_type_at_runtime(recorded_sample) -> None:  # type: ignore[no-untyped-def]
    request = recorded_sample.perception_request()
    assert isinstance(request, UnknownTargetPerceptionRequest)
    assert set(request.model_dump()) == {
        "schema_version",
        "sample_id",
        "audio",
        "language_hint",
        "timeout_seconds",
    }

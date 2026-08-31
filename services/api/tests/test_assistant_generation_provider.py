from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from benma_api.assistant_generation.contracts import AssistantResponseGenerationInput
from benma_api.assistant_generation.factory import build_assistant_response_generator
from benma_api.assistant_generation.openai import OpenAIAssistantResponseGenerator
from benma_api.config import Settings
from benma_api.errors import (
    ProviderMalformedResponseError,
    ProviderRejectedError,
    ProviderTimeoutError,
)


def _provider_response(evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": "resp_fixture",
        "model": "model-provider-revision",
        "status": "completed",
        "output": [
            {
                "type": "message",
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps(evidence, ensure_ascii=False),
                    }
                ],
            }
        ],
    }


def _request(
    *,
    decision: str = "infer",
    perceived: str = "我想卖水果。",
    resolved: str | None = "我想买水果。",
    generation_type: str = "reply",
    clarification_alternatives: tuple[str, ...] = (),
) -> AssistantResponseGenerationInput:
    return AssistantResponseGenerationInput(
        conversation_context_snapshot={
            "format": "benma.conversation-context",
            "version": 1,
            "turns": [{"role": "assistant", "text": "你今天要去超市吗？"}],
        },
        perceived_transcript=perceived,
        contextual_decision=decision,  # type: ignore[arg-type]
        resolved_semantic_text=resolved,
        clarification_alternatives=clarification_alternatives,
        generation_type=generation_type,  # type: ignore[arg-type]
    )


def _generator(
    transport: httpx.MockTransport,
    *,
    api_key: str = "assistant-generation-test-secret",
) -> OpenAIAssistantResponseGenerator:
    return OpenAIAssistantResponseGenerator(
        api_key,
        model="assistant-model-test",
        timeout_seconds=8,
        generator_version="assistant-policy-test",
        reasoning_effort="low",
        transport=transport,
    )


def test_openai_generator_uses_strict_schema_and_server_created_input_only() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json=_provider_response(
                {
                    "generation_type": "reply",
                    "generated_text": "好呀，你想买什么水果？",
                    "clarification_alternatives_used": [],
                }
            ),
        )

    response = _generator(httpx.MockTransport(handler)).generate(_request())

    assert response.evidence.generation_type == "reply"
    assert response.evidence.generated_text == "好呀，你想买什么水果？"
    assert response.provider_version == "model-provider-revision"
    body = captured["body"]
    assert isinstance(body, dict)
    model_input = json.loads(body["input"])
    assert set(model_input) == {
        "format",
        "version",
        "conversation_context",
        "current_user_turn",
        "generation_type",
    }
    assert model_input["current_user_turn"] == {
        "perceived_transcript": "我想卖水果。",
        "contextual_decision": "infer",
        "resolved_semantic_text": "我想买水果。",
        "clarification_alternatives": [],
    }
    serialized = json.dumps(body, ensure_ascii=False)
    assert "perception_run_id" not in serialized
    assert "conversation_id" not in serialized
    assert "raw_payload" not in serialized
    assert "pronunciation" not in serialized.lower()
    assert "user_correction" not in serialized
    assert "assistant-generation-test-secret" not in serialized
    assert body["store"] is False
    assert body["reasoning"] == {"effort": "low"}
    assert "not a language teacher" in body["instructions"]
    assert "Do not automatically correct grammar" in body["instructions"]
    assert "smallest concise" in body["instructions"]
    assert "Never introduce another candidate intended phrase" in body["instructions"]
    output_format = body["text"]["format"]
    assert output_format["type"] == "json_schema"
    assert output_format["strict"] is True
    schema = output_format["schema"]
    assert schema["additionalProperties"] is False
    assert schema["properties"]["generation_type"]["enum"] == [
        "reply",
        "clarification",
    ]
    assert set(schema["required"]) == {
        "generation_type",
        "generated_text",
        "clarification_alternatives_used",
    }


def test_openai_generator_builds_clarification_without_resolved_meaning() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json=_provider_response(
                {
                    "generation_type": "clarification",
                    "generated_text": "你刚才是想说什么呢？",
                    "clarification_alternatives_used": [],
                }
            ),
        )

    request = _request(
        decision="clarify",
        perceived="糟妹。",
        resolved=None,
        generation_type="clarification",
    )
    result = _generator(httpx.MockTransport(handler)).generate(request)

    assert result.evidence.generation_type == "clarification"
    assert result.evidence.clarification_alternatives_used == ()
    model_input = json.loads(captured["body"]["input"])
    assert model_input["current_user_turn"]["resolved_semantic_text"] is None
    assert model_input["current_user_turn"]["clarification_alternatives"] == []


@pytest.mark.parametrize(
    "evidence",
    [
        {
            "generation_type": "clarification",
            "generated_text": "你是想说“糟糕”吗？",
            "clarification_alternatives_used": ["糟糕"],
        },
        {
            "generation_type": "clarification",
            "generated_text": "你是想说“糟糕”吗？",
            "clarification_alternatives_used": [],
        },
    ],
)
def test_clarification_without_alternatives_rejects_candidate_injection(
    evidence: dict[str, Any],
) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=_provider_response(evidence))
    )
    request = _request(
        decision="clarify",
        perceived="糟妹。",
        resolved=None,
        generation_type="clarification",
    )

    with pytest.raises(ProviderMalformedResponseError, match="output contract"):
        _generator(transport).generate(request)


def test_clarification_may_use_exact_grounded_alternatives() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json=_provider_response(
                {
                    "generation_type": "clarification",
                    "generated_text": "你是想说“早梅”还是“糟糕”？",
                    "clarification_alternatives_used": ["早梅", "糟糕"],
                }
            ),
        )
    )
    request = _request(
        decision="clarify",
        perceived="糟妹。",
        resolved=None,
        generation_type="clarification",
        clarification_alternatives=("早梅", "糟糕"),
    )

    result = _generator(transport).generate(request)

    assert result.evidence.clarification_alternatives_used == ("早梅", "糟糕")


@pytest.mark.parametrize(
    "evidence",
    [
        {
            "generation_type": "reply",
            "generated_text": "",
            "clarification_alternatives_used": [],
        },
        {"generation_type": "clarification", "generated_text": "你是指什么？"},
        {
            "generation_type": "reply",
            "generated_text": "好呀！",
            "clarification_alternatives_used": [],
            "extra": True,
        },
    ],
)
def test_openai_generator_rejects_malformed_or_mismatched_output(
    evidence: dict[str, Any],
) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=_provider_response(evidence))
    )
    with pytest.raises(ProviderMalformedResponseError, match="output contract"):
        _generator(transport).generate(_request())


def test_openai_generator_maps_non_json_response() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, text="not JSON")
    )
    with pytest.raises(ProviderMalformedResponseError, match="non-JSON"):
        _generator(transport).generate(_request())


def test_openai_generator_maps_timeout_without_leaking_secret() -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout(
            "transport included assistant-generation-test-secret", request=request
        )

    with pytest.raises(ProviderTimeoutError) as error:
        _generator(httpx.MockTransport(timeout)).generate(_request())

    assert error.value.retryable is True
    assert "assistant-generation-test-secret" not in error.value.message


@pytest.mark.parametrize(("status_code", "retryable"), [(400, False), (429, True), (503, True)])
def test_openai_generator_maps_rejection_safely(
    status_code: int,
    retryable: bool,
) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            status_code,
            json={"error": {"message": "provider-private-detail"}},
        )
    )
    with pytest.raises(ProviderRejectedError) as error:
        _generator(transport).generate(_request())

    assert error.value.retryable is retryable
    assert "provider-private-detail" not in error.value.message


def test_assistant_generator_factory_uses_isolated_settings() -> None:
    settings = Settings(
        _env_file=None,
        assistant_generation_provider="openai",
        openai_api_key="factory-secret",
        openai_assistant_generation_model="model-from-settings",
        openai_assistant_generation_reasoning_effort="none",
        assistant_generation_timeout_seconds=13,
        assistant_generation_policy_version="policy-from-settings",
    )

    generator = build_assistant_response_generator(settings)

    assert generator.provider_name == "openai"
    assert generator.product_name == "responses"
    assert generator.generator_version == "policy-from-settings"
    assert generator.generator_configuration["model"] == "model-from-settings"
    assert generator.generator_configuration["reasoning_effort"] == "none"
    assert generator.generator_configuration["timeout_seconds"] == 13
    assert "factory-secret" not in str(generator.generator_configuration)

from __future__ import annotations

import json
import uuid
from typing import Any

import httpx
import pytest
from conftest import ApiClient

from benma_api.api.routes import get_contextual_interpreter
from benma_api.config import Settings
from benma_api.contextual_interpretation.contracts import ContextualInterpretationInput
from benma_api.contextual_interpretation.factory import build_contextual_interpreter
from benma_api.contextual_interpretation.openai import OpenAIContextualInterpreter
from benma_api.errors import (
    ProviderMalformedResponseError,
    ProviderRejectedError,
    ProviderTimeoutError,
)


def _provider_response(evidence: dict[str, Any]) -> dict[str, Any]:
    return {
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
    perceived: str = "我想卖水果。",
    context: dict[str, Any] | None = None,
) -> ContextualInterpretationInput:
    return ContextualInterpretationInput(
        perception_run_id=uuid.uuid4(),
        perceived_transcript=perceived,
        perception_evidence_snapshot={
            "tokens": [{"token": "卖", "logprob": -2.1}],
            "provider_uncertainty": {"source": "normalized-only"},
        },
        context_snapshot=context or {"situation": "buying fruit at a supermarket"},
    )


def _interpreter(
    handler: httpx.MockTransport,
    *,
    api_key: str = "openai-test-secret",
) -> OpenAIContextualInterpreter:
    return OpenAIContextualInterpreter(
        api_key,
        model="context-model-test",
        timeout_seconds=7,
        interpreter_version="policy-test",
        reasoning_effort="low",
        transport=handler,
    )


def test_openai_interpreter_uses_strict_schema_and_only_allowed_model_inputs() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers)
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json=_provider_response(
                {
                    "decision": "infer",
                    "inferred_text": "我想买水果。",
                    "uncertainty": {
                        "level": "low",
                        "rationale": "The shopping context strongly supports buying.",
                        "alternatives": [],
                    },
                    "clarification_needed": False,
                }
            ),
        )

    interpreter = _interpreter(httpx.MockTransport(handler))
    result = interpreter.interpret(_request())

    assert result.decision == "infer"
    assert result.inferred_text == "我想买水果。"
    assert result.clarification_needed is False
    body = captured["body"]
    assert isinstance(body, dict)
    model_input = json.loads(body["input"])
    assert set(model_input) == {
        "perceived_transcript",
        "perception_evidence_snapshot",
        "context_snapshot",
    }
    assert model_input["perceived_transcript"] == "我想卖水果。"
    assert model_input["perception_evidence_snapshot"]["tokens"] == [
        {"token": "卖", "logprob": -2.1}
    ]
    serialized = json.dumps(body, ensure_ascii=False)
    assert "perception_run_id" not in serialized
    assert "raw_payload" not in serialized
    assert "original_target" not in serialized
    assert "user_correction" not in serialized
    assert "openai-test-secret" not in serialized
    assert body["store"] is False
    assert body["reasoning"] == {"effort": "low"}
    assert "semantically opaque" in body["instructions"]
    assert "merely unusual or ungrammatical" in body["instructions"]
    output_format = body["text"]["format"]
    assert output_format["type"] == "json_schema"
    assert output_format["strict"] is True
    schema = output_format["schema"]
    assert schema["additionalProperties"] is False
    assert schema["properties"]["decision"]["enum"] == [
        "preserve",
        "infer",
        "clarify",
    ]
    assert set(schema["required"]) == {
        "decision",
        "inferred_text",
        "uncertainty",
        "clarification_needed",
    }


@pytest.mark.parametrize(
    ("payload", "expected_decision", "expected_text", "expected_clarification"),
    [
        (
            {
                "decision": "preserve",
                "inferred_text": "我们可以睡觉一起。",
                "uncertainty": {
                    "level": "low",
                    "rationale": "Unusual grammar alone is not contrary evidence.",
                    "alternatives": [],
                },
                "clarification_needed": False,
            },
            "preserve",
            "我们可以睡觉一起。",
            False,
        ),
        (
            {
                "decision": "clarify",
                "inferred_text": None,
                "uncertainty": {
                    "level": "high",
                    "rationale": "The evidence does not establish one intended phrase.",
                    "alternatives": [],
                },
                "clarification_needed": True,
            },
            "clarify",
            None,
            True,
        ),
    ],
)
def test_openai_interpreter_preserve_and_clarify_decisions(
    payload: dict[str, Any],
    expected_decision: str,
    expected_text: str | None,
    expected_clarification: bool,
) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=_provider_response(payload))
    )
    perceived = "我们可以睡觉一起。" if expected_decision == "preserve" else "糟妹。"
    result = _interpreter(transport).interpret(
        _request(perceived=perceived, context={"situation": "ordinary conversation"})
    )

    assert result.decision == expected_decision
    assert result.inferred_text == expected_text
    assert result.clarification_needed is expected_clarification


def test_openai_interpreter_rejects_invalid_decision_combination() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json=_provider_response(
                {
                    "decision": "infer",
                    "inferred_text": None,
                    "uncertainty": {
                        "level": "unknown",
                        "rationale": None,
                        "alternatives": [],
                    },
                    "clarification_needed": False,
                }
            ),
        )
    )

    with pytest.raises(ProviderMalformedResponseError, match="output contract"):
        _interpreter(transport).interpret(_request())


def test_openai_interpreter_maps_timeout_without_leaking_key() -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("transport included openai-test-secret", request=request)

    with pytest.raises(ProviderTimeoutError) as error:
        _interpreter(httpx.MockTransport(timeout)).interpret(_request())

    assert error.value.retryable is True
    assert "openai-test-secret" not in error.value.message


def test_contextual_interpreter_factory_uses_isolated_settings() -> None:
    settings = Settings(
        _env_file=None,
        contextual_interpretation_provider="openai",
        openai_api_key="factory-secret",
        openai_contextual_interpretation_model="model-from-settings",
        openai_contextual_interpretation_reasoning_effort="none",
        contextual_interpretation_timeout_seconds=11,
        contextual_interpretation_version="policy-from-settings",
    )

    interpreter = build_contextual_interpreter(settings)

    assert interpreter.interpreter_name == "openai"
    assert interpreter.interpreter_version == "policy-from-settings"
    assert interpreter.interpreter_configuration["model"] == "model-from-settings"
    assert interpreter.interpreter_configuration["reasoning_effort"] == "none"
    assert interpreter.interpreter_configuration["timeout_seconds"] == 11
    assert "factory-secret" not in str(interpreter.interpreter_configuration)


def test_openai_api_failure_uses_benma_error_envelope_without_secret(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
) -> None:
    secret = "api-envelope-secret"

    def rejected(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"message": f"invalid credential {secret}"}},
        )

    interpreter = _interpreter(httpx.MockTransport(rejected), api_key=secret)
    client.app.dependency_overrides[get_contextual_interpreter] = lambda: interpreter
    perception = client.post(
        f"/v1/utterances/{uploaded_utterance['id']}/perceptions",
        headers=auth_header,
        json={},
    ).json()

    response = client.post(
        f"/v1/perceptions/{perception['id']}/contextual-interpretations",
        headers=auth_header,
        json={"context_snapshot": {"topic": "fruit shopping"}},
    )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "provider_rejected_request"
    assert response.json()["error"]["retryable"] is False
    assert secret not in response.text


def test_openai_rejection_retryability_is_status_based() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(429, json={"error": {"message": "quota detail"}})
    )

    with pytest.raises(ProviderRejectedError) as error:
        _interpreter(transport).interpret(_request())

    assert error.value.retryable is True
    assert "quota detail" not in error.value.message

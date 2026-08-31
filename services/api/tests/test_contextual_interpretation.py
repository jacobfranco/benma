from __future__ import annotations

import dataclasses
import uuid

import pytest
from conftest import ApiClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from benma_api.api.routes import get_contextual_interpreter
from benma_api.config import Settings
from benma_api.contextual_interpretation.contracts import (
    ContextualInterpretationEvidence,
    ContextualInterpretationInput,
)
from benma_api.contextual_interpretation.repository import (
    SqlContextualInterpretationRepository,
)
from benma_api.contextual_interpretation.service import ContextualInterpretationService
from benma_api.db.models import (
    ContextualInterpretationRun,
    PerceptionRun,
    PronunciationInterpretationRun,
)
from benma_api.errors import AnalysisUnsupportedError
from benma_api.speech.contracts import UnknownTargetPerceptionInput


@pytest.fixture(autouse=True)
def configured_contextual_interpreter(client: ApiClient):  # type: ignore[no-untyped-def]
    class Interpreter:
        interpreter_name = "fixture-contextual-interpreter"
        interpreter_version = "1"

        def __init__(self) -> None:
            self.interpreter_configuration = {"temperature": 0}

        def interpret(
            self, request: ContextualInterpretationInput
        ) -> ContextualInterpretationEvidence:
            clarification_needed = request.context_snapshot.get("ambiguous") is True
            preserve = request.context_snapshot.get("preserve") is True
            return ContextualInterpretationEvidence(
                decision=(
                    "clarify" if clarification_needed else "preserve" if preserve else "infer"
                ),
                inferred_text=(
                    None
                    if clarification_needed
                    else request.perceived_transcript
                    if preserve
                    else "我明天想去北京。"
                ),
                uncertainty={
                    "level": "high" if clarification_needed else "medium",
                    "rationale": "Context makes 北京 more plausible than 背景.",
                    "alternatives": ["北京", "北境"]
                    if clarification_needed
                    else ["我明天想去背景。"],
                },
                clarification_needed=clarification_needed,
            )

    client.app.dependency_overrides[get_contextual_interpreter] = Interpreter
    yield
    client.app.dependency_overrides.pop(get_contextual_interpreter, None)


def create_perception(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
) -> dict[str, object]:
    response = client.post(
        f"/v1/utterances/{uploaded_utterance['id']}/perceptions",
        headers=auth_header,
        json={},
    )
    assert response.status_code == 201
    return response.json()


def interpretation_body(
    *,
    clarification_needed: bool = False,
    preserve: bool = False,
) -> dict[str, object]:
    context_snapshot: dict[str, object] = {
        "recent_turns": [{"speaker": "assistant", "text": "你明天想去哪个城市?"}]
    }
    if clarification_needed:
        context_snapshot["ambiguous"] = True
    if preserve:
        context_snapshot["preserve"] = True
    return {
        "context_snapshot": context_snapshot,
    }


def test_contextual_interpretation_preserves_perception_and_can_differ(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    perception = create_perception(client, auth_header, uploaded_utterance)
    response = client.post(
        f"/v1/perceptions/{perception['id']}/contextual-interpretations",
        headers=auth_header,
        json=interpretation_body(),
    )

    assert response.status_code == 201
    interpretation = response.json()
    assert perception["transcript"] == "我明天想去背景。"
    assert interpretation["perception_run_id"] == perception["id"]
    assert interpretation["decision"] == "infer"
    assert interpretation["inferred_text"] == "我明天想去北京。"
    assert interpretation["inferred_text"] != perception["transcript"]

    fetched = client.get(f"/v1/perceptions/{perception['id']}", headers=auth_header)
    assert fetched.status_code == 200
    assert fetched.json()["transcript"] == "我明天想去背景。"
    with session_factory() as db:
        raw = db.get(PerceptionRun, uuid.UUID(str(perception["id"])))
        stored = db.get(
            ContextualInterpretationRun,
            uuid.UUID(interpretation["id"]),
        )
        assert raw is not None and raw.transcript == "我明天想去背景。"
        assert stored is not None and stored.inferred_text == "我明天想去北京。"


def test_contextual_interpretation_can_request_clarification(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
) -> None:
    perception = create_perception(client, auth_header, uploaded_utterance)
    body = interpretation_body(clarification_needed=True)
    response = client.post(
        f"/v1/perceptions/{perception['id']}/contextual-interpretations",
        headers=auth_header,
        json=body,
    )

    assert response.status_code == 201
    assert response.json()["decision"] == "clarify"
    assert response.json()["inferred_text"] is None
    assert response.json()["clarification_needed"] is True
    assert response.json()["uncertainty"]["level"] == "high"


def test_contextual_interpretation_can_preserve(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
) -> None:
    perception = create_perception(client, auth_header, uploaded_utterance)
    response = client.post(
        f"/v1/perceptions/{perception['id']}/contextual-interpretations",
        headers=auth_header,
        json=interpretation_body(preserve=True),
    )

    assert response.status_code == 201
    assert response.json()["decision"] == "preserve"
    assert response.json()["inferred_text"] == perception["transcript"]
    assert response.json()["clarification_needed"] is False


def test_contextual_interpretation_request_cannot_replace_raw_transcript(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
) -> None:
    perception = create_perception(client, auth_header, uploaded_utterance)
    body = interpretation_body()
    body["transcript"] = "rewritten perception"
    response = client.post(
        f"/v1/perceptions/{perception['id']}/contextual-interpretations",
        headers=auth_header,
        json=body,
    )

    assert response.status_code == 422
    fetched = client.get(f"/v1/perceptions/{perception['id']}", headers=auth_header)
    assert fetched.json()["transcript"] == "我明天想去背景。"


def test_contextual_interpreter_is_explicitly_unconfigured_by_default() -> None:
    with pytest.raises(AnalysisUnsupportedError, match="not configured"):
        get_contextual_interpreter(Settings(contextual_interpretation_provider="disabled"))


@pytest.mark.parametrize(
    ("decision", "inferred_text", "clarification_needed"),
    [
        ("infer", None, False),
        ("infer", "我想买水果。", True),
        ("preserve", "我想卖水果。", True),
        ("clarify", None, False),
    ],
)
def test_invalid_decision_combinations_are_rejected(
    decision: str,
    inferred_text: str | None,
    clarification_needed: bool,
) -> None:
    with pytest.raises(ValueError):
        ContextualInterpretationEvidence(
            decision=decision,  # type: ignore[arg-type]
            inferred_text=inferred_text,
            uncertainty={"level": "unknown", "rationale": None, "alternatives": []},
            clarification_needed=clarification_needed,
        )


def test_interpreter_receives_normalized_uncertainty_without_semantic_leakage(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    perception_response = create_perception(client, auth_header, uploaded_utterance)
    perception_id = uuid.UUID(str(perception_response["id"]))

    class Interpreter:
        interpreter_name = "future-llm-adapter"
        interpreter_version = "model-1"

        def __init__(self) -> None:
            self.interpreter_configuration = {"temperature": 0}

        def interpret(
            self, request: ContextualInterpretationInput
        ) -> ContextualInterpretationEvidence:
            assert request.perceived_transcript == "我明天想去背景。"
            assert request.context_snapshot["topic"] == "travel"
            snapshot = request.perception_evidence_snapshot
            assert snapshot["provider_uncertainty"] == {
                "logprobs": [{"token": "背景", "logprob": -2.4}]
            }
            assert snapshot["tokens"] == [{"token": "背景", "logprob": -2.4}]
            assert snapshot["alternatives"] == [{"transcript": "我明天想去北京。"}]
            assert "must_not_leak" not in str(snapshot)
            tokens = snapshot["tokens"]
            assert isinstance(tokens, list)
            tokens[0]["logprob"] = 0
            return ContextualInterpretationEvidence(
                decision="infer",
                inferred_text="我明天想去北京。",
                uncertainty={"level": "low", "rationale": None, "alternatives": []},
                clarification_needed=False,
            )

    with session_factory() as db:
        perception = db.get(PerceptionRun, perception_id)
        assert perception is not None
        uncertainty = {"logprobs": [{"token": "背景", "logprob": -2.4}]}
        uncertain_perception = PerceptionRun(
            account_id=perception.account_id,
            utterance_id=perception.utterance_id,
            provider="uncertainty-fixture",
            product="normalized-fixture",
            adapter_version="1",
            transcript=perception.transcript,
            alternatives=[{"transcript": "我明天想去北京。"}],
            provider_uncertainty=uncertainty,
            normalized_result={
                "transcript": perception.transcript,
                "alternatives": [{"transcript": "我明天想去北京。"}],
                "tokens": [{"token": "背景", "logprob": -2.4}],
                "provider_uncertainty": uncertainty,
                "detected_language": "zh",
                "evidence_status": "live_provider",
            },
            raw_payload_json={"must_not_leak": True},
            status="succeeded",
        )
        db.add(uncertain_perception)
        db.commit()
        run = ContextualInterpretationService(SqlContextualInterpretationRepository(db)).run(
            account_id=perception.account_id,
            perception_run_id=uncertain_perception.id,
            context_snapshot={"topic": "travel"},
            interpreter=Interpreter(),
        )
        assert run.inferred_text == "我明天想去北京。"
        assert uncertain_perception.transcript == "我明天想去背景。"
        assert uncertain_perception.normalized_result is not None
        assert uncertain_perception.normalized_result["tokens"] == [
            {"token": "背景", "logprob": -2.4}
        ]

    unknown_fields = {field.name for field in dataclasses.fields(UnknownTargetPerceptionInput)}
    assert unknown_fields == {
        "utterance_id",
        "canonical_audio",
        "mime_type",
        "language_hint",
        "timeout_seconds",
    }


def test_contextual_interpretations_are_append_only(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    perception = create_perception(client, auth_header, uploaded_utterance)
    interpretation = client.post(
        f"/v1/perceptions/{perception['id']}/contextual-interpretations",
        headers=auth_header,
        json=interpretation_body(),
    ).json()

    with session_factory() as db:
        run = db.get(ContextualInterpretationRun, uuid.UUID(interpretation["id"]))
        assert run is not None
        run.inferred_text = "rewritten"
        with pytest.raises(ValueError, match="append-only"):
            db.commit()


def test_contextual_interpretation_ownership_matches_perception_api(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
) -> None:
    perception = create_perception(client, auth_header, uploaded_utterance)
    interpretation = client.post(
        f"/v1/perceptions/{perception['id']}/contextual-interpretations",
        headers=auth_header,
        json=interpretation_body(),
    ).json()
    other_auth = client.post("/v1/dev/auth", json={"phone_number": "+12025550124"}).json()
    other = {"Authorization": f"Bearer {other_auth['token']}"}

    cross_account_create = client.post(
        f"/v1/perceptions/{perception['id']}/contextual-interpretations",
        headers=other,
        json=interpretation_body(),
    )
    cross_account_get = client.get(
        f"/v1/contextual-interpretations/{interpretation['id']}", headers=other
    )
    assert cross_account_create.status_code == 404
    assert cross_account_get.status_code == 404
    assert cross_account_create.json()["error"]["code"] == "authorization_error"
    assert cross_account_get.json()["error"]["code"] == "authorization_error"

    owned_get = client.get(
        f"/v1/contextual-interpretations/{interpretation['id']}", headers=auth_header
    )
    assert owned_get.status_code == 200
    assert owned_get.json()["perception_run_id"] == perception["id"]


def test_contextual_interpretation_references_owned_perception(
    client: ApiClient,
    auth_header: dict[str, str],
) -> None:
    response = client.post(
        f"/v1/perceptions/{uuid.uuid4()}/contextual-interpretations",
        headers=auth_header,
        json=interpretation_body(),
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "authorization_error"


def test_contextual_run_is_distinct_from_pronunciation_interpretation(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    perception = create_perception(client, auth_header, uploaded_utterance)
    client.post(
        f"/v1/perceptions/{perception['id']}/contextual-interpretations",
        headers=auth_header,
        json=interpretation_body(),
    )
    with session_factory() as db:
        assert db.scalar(select(ContextualInterpretationRun)) is not None
        assert db.scalar(select(PronunciationInterpretationRun)) is None

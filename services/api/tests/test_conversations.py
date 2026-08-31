from __future__ import annotations

import json
import uuid
from copy import deepcopy

import pytest
from conftest import ApiClient
from sqlalchemy.orm import Session, sessionmaker

from benma_api.api.routes import get_contextual_interpreter
from benma_api.contextual_interpretation.contracts import (
    ContextualInterpretationEvidence,
    ContextualInterpretationInput,
)
from benma_api.conversation.context import (
    CONVERSATION_CONTEXT_FORMAT,
    CONVERSATION_CONTEXT_VERSION,
    ConversationContextBuilder,
    resolved_user_turn_text,
)
from benma_api.conversation.service import ConversationService
from benma_api.db.models import (
    Account,
    AssessmentRun,
    ContextualInterpretationRun,
    Conversation,
    PerceptionRun,
    PronunciationAttempt,
    PronunciationTarget,
    UserCorrection,
    Utterance,
)


class RecordingInterpreter:
    interpreter_name = "recording-contextual-interpreter"
    interpreter_version = "conversation-test-v1"

    def __init__(self, decisions: list[str]) -> None:
        self.interpreter_configuration = {"temperature": 0}
        self.decisions = iter(decisions)
        self.requests: list[ContextualInterpretationInput] = []

    def interpret(
        self, request: ContextualInterpretationInput
    ) -> ContextualInterpretationEvidence:
        self.requests.append(deepcopy(request))
        decision = next(self.decisions)
        return ContextualInterpretationEvidence(
            decision=decision,  # type: ignore[arg-type]
            inferred_text=(
                "我想买水果。"
                if decision == "infer"
                else request.perceived_transcript
                if decision == "preserve"
                else None
            ),
            uncertainty={"level": "low", "rationale": None, "alternatives": []},
            clarification_needed=decision == "clarify",
        )


def use_interpreter(client: ApiClient, interpreter: RecordingInterpreter) -> None:
    async def override() -> RecordingInterpreter:
        return interpreter

    client.app.dependency_overrides[get_contextual_interpreter] = override


def create_conversation(client: ApiClient, headers: dict[str, str]) -> dict[str, object]:
    response = client.post("/v1/conversations", headers=headers, json={})
    assert response.status_code == 201, response.text
    return response.json()


def add_assistant_turn(
    session_factory: sessionmaker[Session],
    conversation: dict[str, object],
    text: str,
) -> tuple[uuid.UUID, int]:
    with session_factory() as db:
        turn = ConversationService(db).add_assistant_turn(
            account_id=uuid.UUID(str(conversation["account_id"])),
            conversation_id=uuid.UUID(str(conversation["id"])),
            text=text,
        )
        return turn.id, turn.sequence_number


def add_user_turn(
    client: ApiClient,
    headers: dict[str, str],
    conversation_id: object,
    utterance_id: object,
    perception_id: object,
) -> dict[str, object]:
    response = client.post(
        f"/v1/conversations/{conversation_id}/user-turns",
        headers=headers,
        json={
            "utterance_id": str(utterance_id),
            "perception_run_id": str(perception_id),
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def append_perception(
    session_factory: sessionmaker[Session],
    *,
    utterance_id: object,
    transcript: str,
    raw_marker: str | None = None,
) -> uuid.UUID:
    with session_factory() as db:
        utterance = db.get(Utterance, uuid.UUID(str(utterance_id)))
        assert utterance is not None
        run = PerceptionRun(
            account_id=utterance.account_id,
            utterance_id=utterance.id,
            provider="conversation-fixture",
            product="conversation-fixture",
            adapter_version="1",
            transcript=transcript,
            normalized_result={"transcript": transcript},
            raw_payload_json={"raw_provider_marker": raw_marker} if raw_marker else None,
            status="succeeded",
        )
        db.add(run)
        db.commit()
        return run.id


@pytest.mark.parametrize(
    ("decision", "perceived", "inferred", "expected"),
    [
        ("preserve", "immutable perceived text", "ignored inference", "immutable perceived text"),
        ("infer", "immutable perceived text", "contextual text", "contextual text"),
        ("clarify", "immutable perceived text", None, None),
        (None, "immutable perceived text", None, None),
    ],
)
def test_resolved_user_turn_text_is_derived_from_evidence(
    decision: str | None,
    perceived: str,
    inferred: str | None,
    expected: str | None,
) -> None:
    assert (
        resolved_user_turn_text(
            perceived_transcript=perceived,
            decision=decision,
            inferred_text=inferred,
        )
        == expected
    )


def test_conversation_turns_are_owned_and_stably_ordered(
    client: ApiClient,
    auth_header: dict[str, str],
    session_factory: sessionmaker[Session],
) -> None:
    conversation = create_conversation(client, auth_header)
    first = add_assistant_turn(session_factory, conversation, "第一轮")
    second = add_assistant_turn(session_factory, conversation, "第二轮")

    listed = client.get(
        f"/v1/conversations/{conversation['id']}/turns", headers=auth_header
    )
    assert listed.status_code == 200
    assert [turn["id"] for turn in listed.json()] == [str(first[0]), str(second[0])]
    assert [turn["sequence_number"] for turn in listed.json()] == [1, 2]

    other_auth = client.post("/v1/dev/auth", json={"phone_number": "+12025550199"}).json()
    other_headers = {"Authorization": f"Bearer {other_auth['token']}"}
    hidden_get = client.get(
        f"/v1/conversations/{conversation['id']}", headers=other_headers
    )
    hidden_list = client.get(
        f"/v1/conversations/{conversation['id']}/turns", headers=other_headers
    )
    use_interpreter(client, RecordingInterpreter(["preserve"]))
    hidden_append = client.post(
        f"/v1/conversations/{conversation['id']}/user-turns",
        headers=other_headers,
        json={
            "utterance_id": str(uuid.uuid4()),
            "perception_run_id": str(uuid.uuid4()),
        },
    )
    assert [hidden_get.status_code, hidden_list.status_code, hidden_append.status_code] == [
        404,
        404,
        404,
    ]
    assert all(
        response.json()["error"]["code"] == "authorization_error"
        for response in (hidden_get, hidden_list, hidden_append)
    )


def test_preserve_and_infer_produce_ordered_resolved_history_without_mutation(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    interpreter = RecordingInterpreter(["preserve", "infer"])
    use_interpreter(client, interpreter)
    conversation = create_conversation(client, auth_header)
    add_assistant_turn(session_factory, conversation, "你今天要去超市吗?")
    preserved_id = append_perception(
        session_factory,
        utterance_id=uploaded_utterance["id"],
        transcript="我想卖水果。",
    )
    inferred_id = append_perception(
        session_factory,
        utterance_id=uploaded_utterance["id"],
        transcript="然后回家。",
    )

    preserved = add_user_turn(
        client,
        auth_header,
        conversation["id"],
        uploaded_utterance["id"],
        preserved_id,
    )
    inferred = add_user_turn(
        client,
        auth_header,
        conversation["id"],
        uploaded_utterance["id"],
        inferred_id,
    )

    assert preserved["resolved_text"] == "我想卖水果。"
    assert inferred["resolved_text"] == "我想买水果。"
    assert interpreter.requests[1].context_snapshot == {
        "format": CONVERSATION_CONTEXT_FORMAT,
        "version": CONVERSATION_CONTEXT_VERSION,
        "turns": [
            {"role": "assistant", "text": "你今天要去超市吗?"},
            {"role": "user", "text": "我想卖水果。"},
        ],
    }
    with session_factory() as db:
        preserved_raw = db.get(PerceptionRun, preserved_id)
        inferred_raw = db.get(PerceptionRun, inferred_id)
        assert preserved_raw is not None and preserved_raw.transcript == "我想卖水果。"
        assert inferred_raw is not None and inferred_raw.transcript == "然后回家。"


def test_user_turn_api_rejects_client_supplied_context(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    interpreter = RecordingInterpreter(["preserve"])
    use_interpreter(client, interpreter)
    conversation = create_conversation(client, auth_header)
    perception_id = append_perception(
        session_factory,
        utterance_id=uploaded_utterance["id"],
        transcript="真实感知。",
    )

    response = client.post(
        f"/v1/conversations/{conversation['id']}/user-turns",
        headers=auth_header,
        json={
            "utterance_id": str(uploaded_utterance["id"]),
            "perception_run_id": str(perception_id),
            "context_snapshot": {"turns": [{"role": "assistant", "text": "伪造历史"}]},
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert interpreter.requests == []


def test_clarification_turn_is_explicitly_unresolved_in_later_context(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    interpreter = RecordingInterpreter(["clarify", "preserve"])
    use_interpreter(client, interpreter)
    conversation = create_conversation(client, auth_header)
    unresolved_id = append_perception(
        session_factory,
        utterance_id=uploaded_utterance["id"],
        transcript="绝不能悄悄当作已解决。",
    )
    next_id = append_perception(
        session_factory,
        utterance_id=uploaded_utterance["id"],
        transcript="下一句。",
    )

    unresolved = add_user_turn(
        client,
        auth_header,
        conversation["id"],
        uploaded_utterance["id"],
        unresolved_id,
    )
    add_user_turn(
        client,
        auth_header,
        conversation["id"],
        uploaded_utterance["id"],
        next_id,
    )

    assert unresolved["resolved_text"] is None
    snapshot = interpreter.requests[1].context_snapshot
    assert snapshot["turns"] == [{"role": "user", "unresolved": True}]
    assert "绝不能悄悄当作已解决" not in json.dumps(snapshot, ensure_ascii=False)


def test_context_excludes_raw_pronunciation_corrections_and_current_inference(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    interpreter = RecordingInterpreter(["preserve", "infer"])
    use_interpreter(client, interpreter)
    conversation = create_conversation(client, auth_header)
    add_assistant_turn(session_factory, conversation, "你今天要去超市吗?")
    prior_id = append_perception(
        session_factory,
        utterance_id=uploaded_utterance["id"],
        transcript="先前的真实语义。",
        raw_marker="RAW_PROVIDER_PAYLOAD_MUST_NOT_LEAK",
    )
    current_id = append_perception(
        session_factory,
        utterance_id=uploaded_utterance["id"],
        transcript="我想卖水果。",
    )
    with session_factory() as db:
        utterance = db.get(Utterance, uuid.UUID(str(uploaded_utterance["id"])))
        assert utterance is not None
        correction = UserCorrection(
            account_id=utterance.account_id,
            utterance_id=utterance.id,
            perception_run_id=prior_id,
            intended_text="HIDDEN_USER_CORRECTION_MUST_NOT_LEAK",
        )
        target = PronunciationTarget(
            account_id=utterance.account_id,
            text="HIDDEN_PRONUNCIATION_TARGET_MUST_NOT_LEAK",
            display_pinyin="hidden",
            pinyin_syllables=["hidden"],
            lexical_tones=[None],
            target_source="manual",
            pinyin_source="fixture",
        )
        db.add_all([correction, target])
        db.flush()
        attempt = PronunciationAttempt(
            account_id=utterance.account_id,
            utterance_id=utterance.id,
            target_id=target.id,
        )
        db.add(attempt)
        db.flush()
        db.add(
            AssessmentRun(
                account_id=utterance.account_id,
                pronunciation_attempt_id=attempt.id,
                target_snapshot={"target": "HIDDEN_TARGET_SNAPSHOT_MUST_NOT_LEAK"},
                provider="fixture",
                product="fixture",
                adapter_version="1",
                normalized_result={
                    "pronunciation": "HIDDEN_PRONUNCIATION_EVIDENCE_MUST_NOT_LEAK"
                },
                status="succeeded",
            )
        )
        db.commit()

    add_user_turn(
        client,
        auth_header,
        conversation["id"],
        uploaded_utterance["id"],
        prior_id,
    )
    current = add_user_turn(
        client,
        auth_header,
        conversation["id"],
        uploaded_utterance["id"],
        current_id,
    )

    used_snapshot = interpreter.requests[1].context_snapshot
    serialized = json.dumps(used_snapshot, ensure_ascii=False)
    assert used_snapshot == {
        "format": CONVERSATION_CONTEXT_FORMAT,
        "version": CONVERSATION_CONTEXT_VERSION,
        "turns": [
            {"role": "assistant", "text": "你今天要去超市吗?"},
            {"role": "user", "text": "先前的真实语义。"},
        ],
    }
    assert "RAW_PROVIDER_PAYLOAD_MUST_NOT_LEAK" not in serialized
    assert "HIDDEN_USER_CORRECTION_MUST_NOT_LEAK" not in serialized
    assert "HIDDEN_PRONUNCIATION" not in serialized
    assert "HIDDEN_TARGET_SNAPSHOT_MUST_NOT_LEAK" not in serialized
    assert "我想买水果。" not in serialized
    assert current["resolved_text"] == "我想买水果。"

    with session_factory() as db:
        raw = db.get(PerceptionRun, current_id)
        run = db.get(
            ContextualInterpretationRun,
            uuid.UUID(str(current["contextual_interpretation_run_id"])),
        )
        assert raw is not None and raw.transcript == "我想卖水果。"
        assert run is not None and run.context_snapshot == used_snapshot


def test_context_snapshot_is_deterministic_and_versioned(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as db:
        account = Account(status="active")
        db.add(account)
        db.flush()
        conversation = Conversation(account_id=account.id)
        db.add(conversation)
        db.commit()
        expected = {
            "format": CONVERSATION_CONTEXT_FORMAT,
            "version": CONVERSATION_CONTEXT_VERSION,
            "turns": [],
        }
        builder = ConversationContextBuilder(db)
        assert (
            builder.build(
                account_id=account.id,
                conversation=conversation,
                before_sequence_number=1,
            )
            == expected
        )
        assert (
            builder.build(
                account_id=account.id,
                conversation=conversation,
                before_sequence_number=1,
            )
            == expected
        )

from __future__ import annotations

import json
import threading
import uuid
from collections import Counter

import pytest
from conftest import ApiClient
from sqlalchemy import event, select
from sqlalchemy.orm import Session, sessionmaker
from test_assistant_generation import append_perception, configure_free_talk, create_conversation

from benma_api.db.models import AcousticRun, AssessmentRun, ContextualInterpretationRun
from benma_api.errors import ProviderTimeoutError
from benma_api.pronunciation.acoustics import AutocorrelationAcousticAnalyzer
from benma_api.pronunciation.alignment import ReplayAligner
from benma_api.speech.providers.replay import ReplayPronunciationProvider


def test_acoustic_resource_has_no_target_and_is_owned_and_reused(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    path = f"/v1/utterances/{uploaded_utterance['id']}/acoustics"
    first = client.post(path, headers=auth_header)
    assert first.status_code == 200
    assert first.json()["normalized_result"]["duration_seconds"] > 0
    assert client.post(path, headers=auth_header).json()["id"] == first.json()["id"]
    with session_factory() as db:
        assert len(list(db.scalars(select(AcousticRun)))) == 1
        assert list(db.scalars(select(AssessmentRun))) == []
    other = client.post("/v1/dev/auth", json={"phone_number": "+12025550129"}).json()
    assert (
        client.post(path, headers={"Authorization": f"Bearer {other['token']}"}).status_code == 404
    )


def test_target_computations_overlap_without_worker_sql_or_duplicate_runs(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = client.post(
        "/v1/pronunciation-targets", headers=auth_header, json={"text": "你好"}
    ).json()
    attempt = client.post(
        "/v1/pronunciation-attempts",
        headers=auth_header,
        json={
            "utterance_id": uploaded_utterance["id"],
            "target_id": target["id"],
        },
    ).json()
    barrier = threading.Barrier(3, timeout=3)
    calls: Counter[str] = Counter()
    workers: set[int] = set()
    sql_threads: set[int] = set()
    for cls, method in [
        (ReplayPronunciationProvider, "assess"),
        (AutocorrelationAcousticAnalyzer, "analyze"),
        (ReplayAligner, "align"),
    ]:
        original = getattr(cls, method)

        def concurrent(self, request, _original=original, _method=method):
            calls[_method] += 1
            workers.add(threading.get_ident())
            barrier.wait()  # A sequential implementation cannot pass this barrier.
            return _original(self, request)

        monkeypatch.setattr(cls, method, concurrent)
    engine = session_factory.kw["bind"]

    def record_sql(*_):
        sql_threads.add(threading.get_ident())

    event.listen(engine, "before_cursor_execute", record_sql)
    try:
        path = f"/v1/pronunciation-attempts/{attempt['id']}/analyze"
        first_response = client.post(path, headers=auth_header, json={})
        assert first_response.status_code == 200, first_response.text
        first = first_response.json()
        second = client.post(path, headers=auth_header, json={}).json()
    finally:
        event.remove(engine, "before_cursor_execute", record_sql)
    assert calls == {"assess": 1, "analyze": 1, "align": 1}
    assert len(workers) == 3 and not workers.intersection(sql_threads)
    for name in ("assessment", "acoustic", "alignment"):
        assert first[name]["status"] == "succeeded"
        assert first[name]["id"] == second[name]["id"]
        assert (
            first["interpretation"]["input_evidence_run_ids"][f"{name}_run_id"] == first[name]["id"]
        )
    assert first["assessment"]["target_snapshot"]["text"] == "你好"
    assert first["overall_evidence"]["analysis_wall_ms"] >= 0
    assert "provider_compute_sum_ms" in first["overall_evidence"]


def test_acoustic_failure_keeps_full_target_provider_evidence(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*_):
        raise RuntimeError("unexpected acoustic failure")

    monkeypatch.setattr(AutocorrelationAcousticAnalyzer, "analyze", fail)
    target = client.post(
        "/v1/pronunciation-targets", headers=auth_header, json={"text": "你好"}
    ).json()
    attempt = client.post(
        "/v1/pronunciation-attempts",
        headers=auth_header,
        json={
            "utterance_id": uploaded_utterance["id"],
            "target_id": target["id"],
        },
    ).json()
    response = client.post(
        f"/v1/pronunciation-attempts/{attempt['id']}/analyze", headers=auth_header, json={}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["acoustic"]["status"] == "failed"
    assert result["assessment"]["status"] == result["alignment"]["status"] == "succeeded"
    assert (
        result["interpretation"]["input_evidence_run_ids"]["acoustic_run_id"]
        == result["acoustic"]["id"]
    )


@pytest.mark.parametrize("decision", ["preserve", "infer", "clarify"])
def test_stream_orders_authoritative_interpretation_before_committed_reply(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
    decision: str,
) -> None:
    interpreter, generator = configure_free_talk(
        client, decisions=[decision], outputs=["请继续说。"]
    )
    conversation = create_conversation(client, auth_header)
    perception = append_perception(
        session_factory, utterance_id=uploaded_utterance["id"], transcript="你好，今天我"
    )
    response = client.post(
        f"/v1/conversations/{conversation['id']}/user-turns/stream",
        headers=auth_header,
        json={"utterance_id": uploaded_utterance["id"], "perception_run_id": str(perception)},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    events = [json.loads(line) for line in response.text.splitlines()]
    assert [item["type"] for item in events] == ["interpretation", "complete"]
    assert events[0]["interpretation"]["decision"] == decision
    result = events[1]["result"]
    assert result["perceived_text"] == "你好，今天我"
    assert result["contextual_interpretation_run_id"] == events[0]["interpretation"]["id"]
    assert result["assistant_turn"]["assistant_text"] == "请继续说。"
    assert result["assistant_turn"]["assistant_speech"] is None
    assert len(interpreter.requests) == len(generator.requests) == 1
    if decision == "clarify":
        assert result["resolved_text"] is None
        assert generator.requests[0].generation_type == "clarification"
    # Reconnecting does not reinterpret evidence already linked to a committed turn.
    again = client.post(
        f"/v1/conversations/{conversation['id']}/user-turns/stream",
        headers=auth_header,
        json={"utterance_id": uploaded_utterance["id"], "perception_run_id": str(perception)},
    )
    assert json.loads(again.text)["type"] == "error"
    assert len(interpreter.requests) == len(generator.requests) == 1


def test_stream_generation_failure_keeps_perception_and_rejects_other_account(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    configure_free_talk(
        client, decisions=["clarify"], outputs=[], error=ProviderTimeoutError("private detail")
    )
    conversation = create_conversation(client, auth_header)
    perception = append_perception(
        session_factory, utterance_id=uploaded_utterance["id"], transcript="你好，今天我"
    )
    path = f"/v1/conversations/{conversation['id']}/user-turns/stream"
    body = {"utterance_id": uploaded_utterance["id"], "perception_run_id": str(perception)}
    response = client.post(path, headers=auth_header, json=body)
    events = [json.loads(line) for line in response.text.splitlines()]
    assert [item["type"] for item in events] == ["interpretation", "error"]
    assert "private detail" not in response.text
    assert (
        client.get(f"/v1/perceptions/{perception}", headers=auth_header).json()["transcript"]
        == "你好，今天我"
    )
    with session_factory() as db:
        # The existing generation-failure service commits its failure lineage.
        run = db.get(ContextualInterpretationRun, uuid.UUID(events[0]["interpretation"]["id"]))
        assert run is not None and run.decision == "clarify"
    other = client.post("/v1/dev/auth", json={"phone_number": "+12025550129"}).json()
    assert (
        client.post(
            path, headers={"Authorization": f"Bearer {other['token']}"}, json=body
        ).status_code
        == 404
    )


def test_meaning_bytes_leave_server_while_generation_is_still_running(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, generator = configure_free_talk(client, decisions=["preserve"], outputs=["你好。"])
    conversation = create_conversation(client, auth_header)
    perception = append_perception(
        session_factory, utterance_id=uploaded_utterance["id"], transcript="你好"
    )
    sent = threading.Event()
    original_generate = generator.generate

    def generate(request):
        assert sent.wait(3), "interpretation was buffered behind generation"
        return original_generate(request)

    monkeypatch.setattr(generator, "generate", generate)
    original_stack = client.app.middleware_stack

    async def observe(scope, receive, send):
        async def track(message):
            if message[
                "type"
            ] == "http.response.body" and b'"type":"interpretation"' in message.get("body", b""):
                sent.set()
            await send(message)

        await original_stack(scope, receive, track)

    monkeypatch.setattr(client.app, "middleware_stack", observe)
    response = client.post(
        f"/v1/conversations/{conversation['id']}/user-turns/stream",
        headers=auth_header,
        json={"utterance_id": uploaded_utterance["id"], "perception_run_id": str(perception)},
    )
    assert [json.loads(line)["type"] for line in response.text.splitlines()] == [
        "interpretation",
        "complete",
    ]


def test_utterance_analysis_locks_do_not_block_postgres_perception_foreign_keys(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
) -> None:
    from sqlalchemy.dialects import postgresql

    locks: list[str] = []

    def capture(execution):
        statement = str(execution.statement.compile(dialect=postgresql.dialect()))
        if "FOR " in statement and "FROM utterances" in statement:
            locks.append(statement)

    event.listen(Session, "do_orm_execute", capture)
    try:
        response = client.post(
            f"/v1/utterances/{uploaded_utterance['id']}/acoustics", headers=auth_header
        )
        assert response.status_code == 200
        target = client.post(
            "/v1/pronunciation-targets", headers=auth_header, json={"text": "你好"}
        ).json()
        attempt = client.post(
            "/v1/pronunciation-attempts",
            headers=auth_header,
            json={
                "utterance_id": uploaded_utterance["id"],
                "target_id": target["id"],
            },
        ).json()
        assert (
            client.post(
                f"/v1/pronunciation-attempts/{attempt['id']}/analyze", headers=auth_header, json={}
            ).status_code
            == 200
        )
    finally:
        event.remove(Session, "do_orm_execute", capture)
    # SQLite does not exercise PostgreSQL row locks. Compile the actual statements
    # issued by both workflows: this mode conflicts with another analysis lock,
    # but is compatible with the KEY SHARE lock taken for a perception FK insert.
    assert len(locks) == 2
    assert all(statement.endswith("FOR NO KEY UPDATE") for statement in locks)


def test_progress_openapi_describes_ndjson_events(client: ApiClient) -> None:
    schema = client.app.openapi()
    content = schema["paths"]["/v1/conversations/{conversation_id}/user-turns/stream"]["post"][
        "responses"
    ]["200"]["content"]
    assert set(content) == {"application/x-ndjson"}
    assert content["application/x-ndjson"]["schema"]["$ref"].endswith("/ConversationStreamEvent")

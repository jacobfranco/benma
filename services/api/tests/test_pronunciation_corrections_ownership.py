from __future__ import annotations

import uuid

import pytest
from conftest import ApiClient, wav_bytes
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from benma_api.db.models import (
    AssessmentRun,
    PerceptionRun,
    PronunciationAttempt,
    UserCorrection,
)
from benma_api.errors import ProviderTimeoutError
from benma_api.pronunciation.service import AssessmentService
from benma_api.speech.contracts import AssessmentProviderResponse, KnownTargetAssessmentInput


def test_correction_appends_without_overwriting_perception(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    utterance_id = uploaded_utterance["id"]
    perception = client.post(
        f"/v1/utterances/{utterance_id}/perceptions", headers=auth_header, json={}
    ).json()
    correction = client.post(
        f"/v1/utterances/{utterance_id}/corrections",
        headers=auth_header,
        json={"intended_text": "我明天想去北京。", "perception_run_id": perception["id"]},
    )
    assert correction.status_code == 201
    fetched = client.get(f"/v1/perceptions/{perception['id']}", headers=auth_header)
    assert fetched.json()["transcript"] == "我明天想去背景。"
    with session_factory() as db:
        assert len(list(db.scalars(select(UserCorrection)))) == 1


def test_evidence_rows_are_append_only(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    perception = client.post(
        f"/v1/utterances/{uploaded_utterance['id']}/perceptions",
        headers=auth_header,
        json={},
    ).json()
    with session_factory() as db:
        run = db.get(PerceptionRun, uuid.UUID(perception["id"]))
        assert run is not None
        run.transcript = "rewritten"
        with pytest.raises(ValueError, match="append-only"):
            db.commit()


def test_known_target_flow_preserves_snapshot_and_missing_tones(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    target_response = client.post(
        "/v1/pronunciation-targets", headers=auth_header, json={"text": "生活"}
    )
    assert target_response.status_code == 201
    target = target_response.json()
    assert target["display_pinyin"] == "shēng huó"
    assert target["lexical_tones"] == [1, 2]
    assert target["pinyin_source"] == "pypinyin-automatic"

    attempt = client.post(
        "/v1/pronunciation-attempts",
        headers=auth_header,
        json={"utterance_id": uploaded_utterance["id"], "target_id": target["id"]},
    ).json()
    first = client.post(
        f"/v1/pronunciation-attempts/{attempt['id']}/assessments",
        headers=auth_header,
        json={},
    )
    second = client.post(
        f"/v1/pronunciation-attempts/{attempt['id']}/assessments",
        headers=auth_header,
        json={},
    )
    assert first.status_code == second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
    result = first.json()["normalized_result"]
    assert result["evidence_status"] == "synthetic_replay"
    assert "detected_tone" not in str(result)
    assert "detected lexical tone" in result["unsupported_capabilities"]
    assert first.json()["target_snapshot"]["text"] == "生活"
    with session_factory() as db:
        assert len(list(db.scalars(select(AssessmentRun)))) == 2


def test_cross_account_isolation_for_all_owned_resources(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
) -> None:
    practice = client.post(
        "/v1/practice-sessions",
        headers=auth_header,
        json={"mode": "pronunciation", "metadata": {}},
    ).json()
    perception = client.post(
        f"/v1/utterances/{uploaded_utterance['id']}/perceptions",
        headers=auth_header,
        json={},
    ).json()
    target = client.post(
        "/v1/pronunciation-targets", headers=auth_header, json={"text": "生活"}
    ).json()
    attempt = client.post(
        "/v1/pronunciation-attempts",
        headers=auth_header,
        json={"utterance_id": uploaded_utterance["id"], "target_id": target["id"]},
    ).json()
    other_auth = client.post("/v1/dev/auth", json={"phone_number": "+12025550124"}).json()
    other = {"Authorization": f"Bearer {other_auth['token']}"}
    paths = [
        f"/v1/practice-sessions/{practice['id']}",
        f"/v1/utterances/{uploaded_utterance['id']}",
        f"/v1/utterances/{uploaded_utterance['id']}/audio",
        f"/v1/perceptions/{perception['id']}",
        f"/v1/pronunciation-targets/{target['id']}",
        f"/v1/pronunciation-attempts/{attempt['id']}",
    ]
    for path in paths:
        response = client.get(path, headers=other)
        assert response.status_code == 404, path
        assert response.json()["error"]["code"] == "authorization_error"
    correction = client.post(
        f"/v1/utterances/{uploaded_utterance['id']}/corrections",
        headers=other,
        json={"intended_text": "北京", "perception_run_id": perception["id"]},
    )
    assert correction.status_code == 404


def test_correction_must_match_owned_perception(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
) -> None:
    response = client.post(
        f"/v1/utterances/{uploaded_utterance['id']}/corrections",
        headers=auth_header,
        json={"intended_text": "北京", "perception_run_id": str(uuid.uuid4())},
    )
    assert response.status_code == 404


def test_failed_assessment_persists_and_retry_reuses_attempt(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    target = client.post(
        "/v1/pronunciation-targets", headers=auth_header, json={"text": "生活"}
    ).json()
    attempt = client.post(
        "/v1/pronunciation-attempts",
        headers=auth_header,
        json={"utterance_id": uploaded_utterance["id"], "target_id": target["id"]},
    ).json()

    class FailingProvider:
        provider_name = "failing"
        product_name = "fixture"
        adapter_version = "1"

        def assess(self, request: KnownTargetAssessmentInput) -> AssessmentProviderResponse:
            raise ProviderTimeoutError("offline", retryable=True)

    class MemoryStore:
        def read(self, key: str) -> bytes:
            return wav_bytes()

    with session_factory() as db:
        stored_attempt = db.get(PronunciationAttempt, uuid.UUID(attempt["id"]))
        assert stored_attempt is not None
        with pytest.raises(ProviderTimeoutError):
            AssessmentService(db, MemoryStore(), FailingProvider()).run(  # type: ignore[arg-type]
                account_id=stored_attempt.account_id,
                attempt_id=uuid.UUID(attempt["id"]),
                timeout_seconds=30,
            )
        failed = db.scalar(select(AssessmentRun).where(AssessmentRun.provider == "failing"))
        assert failed is not None and failed.status == "failed"

    retried = client.post(
        f"/v1/pronunciation-attempts/{attempt['id']}/assessments",
        headers=auth_header,
        json={},
    )
    assert retried.status_code == 201
    assert retried.json()["pronunciation_attempt_id"] == attempt["id"]
    with session_factory() as db:
        runs = list(
            db.scalars(
                select(AssessmentRun)
                .where(AssessmentRun.pronunciation_attempt_id == uuid.UUID(attempt["id"]))
                .order_by(AssessmentRun.created_at)
            )
        )
        assert [run.status for run in runs] == ["failed", "succeeded"]

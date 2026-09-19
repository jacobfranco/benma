from __future__ import annotations

import dataclasses
import uuid

import httpx
import pytest
from conftest import ApiClient
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from benma_api.db.models import AudioAsset, PerceptionRun
from benma_api.errors import ProviderUnavailableError
from benma_api.perception.service import PerceptionService
from benma_api.schemas import UnknownPerceptionRequest
from benma_api.speech.contracts import (
    PerceptionEvidence,
    PerceptionProviderResponse,
    UnknownTargetPerceptionInput,
)
from benma_api.speech.providers.openai import (
    OpenAITranscriptionProvider,
    openai_form_fields,
)

FORBIDDEN = {
    "context_snapshot",
    "correction",
    "corrections",
    "target",
    "target_text",
    "intended_text",
    "pinyin",
    "context",
    "prompt",
    "conversation_history",
    "semantic_context",
}


@pytest.mark.parametrize("field", sorted(FORBIDDEN))
def test_unknown_contract_rejects_semantic_fields(field: str) -> None:
    with pytest.raises(ValidationError):
        UnknownPerceptionRequest.model_validate({field: "北京"})


def test_internal_unknown_type_has_no_semantic_slots() -> None:
    fields = {field.name for field in dataclasses.fields(UnknownTargetPerceptionInput)}
    assert fields.isdisjoint(FORBIDDEN)
    assert fields == {
        "utterance_id",
        "canonical_audio",
        "mime_type",
        "language_hint",
        "timeout_seconds",
    }


def test_perception_service_only_loads_canonical_audio() -> None:
    calls: list[str] = []
    runs: list[PerceptionRun] = []
    asset = AudioAsset(
        account_id=uuid.uuid4(),
        storage_key="canonical.wav",
        kind="canonical",
        mime_type="audio/wav",
        sha256="0" * 64,
        size_bytes=4,
    )

    class Repository:
        def load_canonical_asset(self, account_id, utterance_id):  # type: ignore[no-untyped-def]
            calls.append("load_canonical_asset")
            return asset

        def append_run(self, run: PerceptionRun) -> None:
            calls.append("append_run")
            runs.append(run)

    class Store:
        def read(self, key: str) -> bytes:
            calls.append("read_audio")
            return b"wave"

    class Provider:
        provider_name = "capture"
        product_name = "capture"
        adapter_version = "1"

        def perceive(self, request: UnknownTargetPerceptionInput) -> PerceptionProviderResponse:
            calls.append("provider")
            assert {field.name for field in dataclasses.fields(request)}.isdisjoint(FORBIDDEN)
            return PerceptionProviderResponse(
                PerceptionEvidence("你好", None, None, None, None, "zh", "live_provider"),
                {"text": "你好"},
            )

    PerceptionService(Repository(), Store(), Provider()).run(  # type: ignore[arg-type]
        account_id=asset.account_id,
        utterance_id=uuid.uuid4(),
        language_hint="zh",
        timeout_seconds=30,
    )
    assert calls == ["load_canonical_asset", "read_audio", "provider", "append_run"]
    assert runs[0].transcript == "你好"


@pytest.mark.parametrize("transcript", ["你好", "你好，今天我……", "Neal zaigan shima"])  # noqa: RUF001
def test_openai_adapter_serialization_has_no_semantic_hints(
    monkeypatch: pytest.MonkeyPatch,
    transcript: str,
) -> None:
    captured: dict[str, object] = {}

    class Response:
        status_code = 200

        def json(self) -> dict[str, object]:
            return {"text": transcript, "logprobs": [{"token": "你", "logprob": -0.2}]}

    def fake_post(url: str, **kwargs: object) -> Response:
        captured["url"] = url
        captured.update(kwargs)
        return Response()

    monkeypatch.setattr(httpx, "post", fake_post)
    provider = OpenAITranscriptionProvider("test-key")
    response = provider.perceive(
        UnknownTargetPerceptionInput(uuid.uuid4(), b"wav", "audio/wav", "zh", 30)
    )
    assert response.evidence.transcript == transcript
    assert response.evidence.detected_language is None
    data = captured["data"]
    assert isinstance(data, dict)
    from benma_api.speech.providers.openai import MANDARIN_POLICY

    assert data["prompt"] == MANDARIN_POLICY
    assert (set(data) - {"prompt"}).isdisjoint(FORBIDDEN)
    assert set(openai_form_fields("gpt-4o-transcribe", "zh")) == {
        "model",
        "language",
        "response_format",
        "include[]",
        "prompt",
    }


def test_success_retry_appends_and_replay_is_labeled(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    path = f"/v1/utterances/{uploaded_utterance['id']}/perceptions"
    first = client.post(path, headers=auth_header, json={})
    second = client.post(path, headers=auth_header, json={})
    assert first.status_code == second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
    assert first.json()["transcript"] == "我明天想去背景。"
    assert first.json()["normalized_result"]["evidence_status"] == "synthetic_replay"
    with session_factory() as db:
        assert db.scalar(select(func.count()).select_from(PerceptionRun)) == 2


def test_endpoint_rejects_target_field(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
) -> None:
    response = client.post(
        f"/v1/utterances/{uploaded_utterance['id']}/perceptions",
        headers=auth_header,
        json={"target_text": "北京"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_provider_failure_is_persisted(
    session_factory: sessionmaker[Session],
    uploaded_utterance: dict[str, object],
) -> None:
    class FailingProvider:
        provider_name = "failing"
        product_name = "fixture"
        adapter_version = "1"

        def perceive(self, request: UnknownTargetPerceptionInput) -> PerceptionProviderResponse:
            raise ProviderUnavailableError("offline", retryable=True)

    class MemoryStore:
        def read(self, key: str) -> bytes:
            return b"wav"

    from benma_api.perception.repository import SqlPerceptionRepository

    with session_factory() as db:
        asset = db.scalar(select(AudioAsset).where(AudioAsset.kind == "canonical"))
        assert asset is not None
        with pytest.raises(ProviderUnavailableError):
            PerceptionService(
                SqlPerceptionRepository(db),
                MemoryStore(),
                FailingProvider(),  # type: ignore[arg-type]
            ).run(
                account_id=asset.account_id,
                utterance_id=uuid.UUID(str(uploaded_utterance["id"])),
                language_hint="zh",
                timeout_seconds=30,
            )
        failed = db.scalar(select(PerceptionRun).where(PerceptionRun.provider == "failing"))
        assert failed is not None and failed.status == "failed"
        assert failed.error_code == "provider_unavailable"

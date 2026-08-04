from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

import pytest
from conftest import ApiClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from benma_api.db.models import ResearchExport
from benma_api.pronunciation.research_export import export_pronunciation_attempt
from benma_api.storage.audio_store import LocalFilesystemAudioStore


def _attempt(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
) -> uuid.UUID:
    target = client.post(
        "/v1/pronunciation-targets", headers=auth_header, json={"text": "你好"}
    ).json()
    response = client.post(
        "/v1/pronunciation-attempts",
        headers=auth_header,
        json={"utterance_id": uploaded_utterance["id"], "target_id": target["id"]},
    )
    assert response.status_code == 201
    return uuid.UUID(response.json()["id"])


def test_export_requires_confirmation_and_preserves_only_selected_evidence(
    tmp_path: Path,
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
    store: LocalFilesystemAudioStore,
) -> None:
    attempt_id = _attempt(client, auth_header, uploaded_utterance)
    with session_factory() as db, pytest.raises(ValueError, match="explicit"):
        export_pronunciation_attempt(
            db,
            store,
            attempt_id=attempt_id,
            output=tmp_path / "export",
            requested_production="wrong_tone",
            confirmed=False,
        )
    assert not (tmp_path / "export").exists()
    with session_factory() as db:
        destination = export_pronunciation_attempt(
            db,
            store,
            attempt_id=attempt_id,
            output=tmp_path / "export",
            requested_production="wrong_tone",
            confirmed=True,
        )
        exports = list(db.scalars(select(ResearchExport)))
    assert len(exports) == 1
    assert {path.name for path in destination.iterdir()} == {
        "original.wav",
        "canonical.wav",
        "metadata.json",
    }
    metadata = json.loads((destination / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["production_attempt_id"] == str(attempt_id)
    assert metadata["requested_production_is_ground_truth"] is False
    assert metadata["audio"]["canonical_sha256"] == hashlib.sha256(
        (destination / "canonical.wav").read_bytes()
    ).hexdigest()
    serialized = json.dumps(metadata).lower()
    assert "phone_number" not in serialized
    assert "account_id" not in serialized

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import ApiClient, wav_bytes
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from benma_api.audio.service import AudioIngestService
from benma_api.config import Settings
from benma_api.db.models import Account, AudioAsset
from benma_api.errors import InvalidAudioError
from benma_api.storage.audio_store import LocalFilesystemAudioStore


def test_valid_upload_canonicalizes_and_hashes(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
) -> None:
    original = uploaded_utterance["original_audio"]
    canonical = uploaded_utterance["canonical_audio"]
    assert isinstance(original, dict) and isinstance(canonical, dict)
    assert original["sha256"] != ""
    assert canonical["mime_type"] == "audio/wav"
    assert canonical["sample_rate_hz"] == 16000
    assert canonical["channels"] == 1
    assert canonical["sample_width_bits"] == 16
    assert "storage_key" not in str(uploaded_utterance)
    assert client.get(uploaded_utterance["audio_url"], headers=auth_header).content == wav_bytes()


def test_browser_mime_parameters_preserve_bytes_and_canonicalization(
    client: ApiClient, auth_header: dict[str, str]
) -> None:
    payload = wav_bytes()
    response = client.post(
        "/v1/utterances",
        headers=auth_header,
        files={"file": ("recording.wav", payload, "audio/wav;codecs=pcm")},
    )
    assert response.status_code == 201
    utterance = response.json()
    assert utterance["original_audio"]["mime_type"] == "audio/wav"
    assert utterance["canonical_audio"]["mime_type"] == "audio/wav"
    assert utterance["canonical_audio"]["sample_rate_hz"] == 16000
    assert client.get(utterance["audio_url"], headers=auth_header).content == payload


@pytest.mark.parametrize(
    ("payload", "content_type"),
    [
        (b"", "audio/wav"),
        (b"not audio", "audio/wav"),
        (b"anything", "text/plain"),
        (b"anything", "text/plain;codecs=opus"),
    ],
)
def test_invalid_audio_is_rejected(
    client: ApiClient,
    auth_header: dict[str, str],
    payload: bytes,
    content_type: str,
) -> None:
    response = client.post(
        "/v1/utterances",
        headers=auth_header,
        files={"file": ("unsafe-name.wav", payload, content_type)},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_audio"


def test_oversized_upload_is_rejected(
    client: ApiClient, auth_header: dict[str, str], settings: Settings
) -> None:
    settings.max_upload_bytes = 10
    response = client.post(
        "/v1/utterances",
        headers=auth_header,
        files={"file": ("speech.wav", wav_bytes(), "audio/wav")},
    )
    assert response.status_code == 422


def test_overlong_audio_is_rejected(
    client: ApiClient, auth_header: dict[str, str], settings: Settings
) -> None:
    settings.max_audio_duration_seconds = 0.05
    response = client.post(
        "/v1/utterances",
        headers=auth_header,
        files={"file": ("speech.wav", wav_bytes(duration_seconds=0.15), "audio/wav")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_audio"


def test_generated_storage_key_ignores_user_filename(
    uploaded_utterance: dict[str, object],
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as db:
        keys = list(db.scalars(select(AudioAsset.storage_key)))
    assert len(keys) == 2
    assert all(".." not in key and "secrets" not in key for key in keys)


def test_original_survives_canonicalization_failure(
    settings: Settings,
    store: LocalFilesystemAudioStore,
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with session_factory() as db:
        account = Account()
        db.add(account)
        db.commit()

        def fail(*args: object) -> bytes:
            raise InvalidAudioError("forced canonical failure")

        monkeypatch.setattr("benma_api.audio.service.canonicalize", fail)
        with pytest.raises(InvalidAudioError, match="forced"):
            AudioIngestService(db, store, settings).ingest(
                account_id=account.id,
                data=wav_bytes(),
                mime_type="audio/wav",
                practice_session_id=None,
            )
        db.expire_all()
        assets = list(db.scalars(select(AudioAsset)))
        assert len(assets) == 1 and assets[0].kind == "original"
        assert store.path_for_processing(assets[0].storage_key).exists()


def test_store_rejects_path_traversal(tmp_path: Path) -> None:
    store = LocalFilesystemAudioStore(tmp_path / "objects")
    with pytest.raises(ValueError):
        store.put("../escape.wav", b"x")


def test_list_and_get_utterance(
    client: ApiClient,
    auth_header: dict[str, str],
    uploaded_utterance: dict[str, object],
) -> None:
    listed = client.get("/v1/utterances", headers=auth_header)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [uploaded_utterance["id"]]
    fetched = client.get(
        f"/v1/utterances/{uploaded_utterance['id']}", headers=auth_header
    )
    assert fetched.status_code == 200

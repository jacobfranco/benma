from __future__ import annotations

import asyncio
import io
import wave
from collections.abc import Generator
from pathlib import Path

import httpx
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from benma_api.app import create_app
from benma_api.config import Settings, get_request_settings
from benma_api.db.base import Base
from benma_api.db.session import get_db
from benma_api.storage.audio_store import LocalFilesystemAudioStore, get_audio_store


class ApiClient:
    def __init__(self, app) -> None:  # type: ignore[no-untyped-def]
        self.app = app

    def request(self, method: str, path: str, **kwargs: object) -> httpx.Response:
        async def execute() -> httpx.Response:
            transport = httpx.ASGITransport(app=self.app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as client:
                return await client.request(method, path, **kwargs)

        return asyncio.run(execute())

    def get(self, path: str, **kwargs: object) -> httpx.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: object) -> httpx.Response:
        return self.request("POST", path, **kwargs)

    def delete(self, path: str, **kwargs: object) -> httpx.Response:
        return self.request("DELETE", path, **kwargs)


def wav_bytes(duration_seconds: float = 0.15, sample_rate: int = 16000) -> bytes:
    output = io.BytesIO()
    frames = int(duration_seconds * sample_rate)
    with wave.open(output, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate)
        writer.writeframes(b"\x00\x00" * frames)
    return output.getvalue()


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        environment="test",
        database_url="sqlite://",
        audio_storage_dir=tmp_path / "audio",
        dev_auth_enabled=True,
        perception_provider="replay",
        assessment_provider="replay",
        max_upload_bytes=2 * 1024 * 1024,
        max_audio_duration_seconds=5,
    )


@pytest.fixture
def session_factory() -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _):  # type: ignore[no-untyped-def]
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    yield factory
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def store(settings: Settings) -> LocalFilesystemAudioStore:
    return LocalFilesystemAudioStore(settings.audio_storage_dir)


@pytest.fixture
def client(
    settings: Settings,
    session_factory: sessionmaker[Session],
    store: LocalFilesystemAudioStore,
) -> Generator[ApiClient, None, None]:
    app = create_app(settings)

    async def override_db():  # type: ignore[no-untyped-def]
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    async def override_settings() -> Settings:
        return settings

    async def override_store() -> LocalFilesystemAudioStore:
        return store

    app.dependency_overrides[get_request_settings] = override_settings
    app.dependency_overrides[get_audio_store] = override_store
    yield ApiClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_header(client: ApiClient) -> dict[str, str]:
    response = client.post("/v1/dev/auth", json={"phone_number": "+12025550123"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


@pytest.fixture
def uploaded_utterance(client: ApiClient, auth_header: dict[str, str]) -> dict[str, object]:
    response = client.post(
        "/v1/utterances",
        headers=auth_header,
        files={"file": ("speech.wav", wav_bytes(), "audio/wav")},
    )
    assert response.status_code == 201, response.text
    return response.json()

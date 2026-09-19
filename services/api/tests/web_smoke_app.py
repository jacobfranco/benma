"""Local browser harness: real auth/ingest/workflows; deterministic unpaid providers.

Run from services/api: uv run uvicorn --app-dir tests web_smoke_app:app --port 8000.
Never load this fixture app in production. Uses an isolated temporary SQLite database.
"""

import asyncio
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from test_assistant_generation import (
    RecordingSpeechProvider,
    SequencedGenerator,
    SequencedInterpreter,
)

from benma_api.api.routes import (
    get_assistant_response_generator,
    get_assistant_speech_provider,
    get_contextual_interpreter,
)
from benma_api.app import create_app
from benma_api.config import Settings, get_request_settings
from benma_api.db.base import Base
from benma_api.db.session import get_db
from benma_api.speech.providers.replay import ReplayPerceptionProvider
from benma_api.storage.audio_store import LocalFilesystemAudioStore, get_audio_store


class ExamplePerception(ReplayPerceptionProvider):
    def perceive(self, request):
        response = super().perceive(request)
        text = "你好，今天我们聊聊周末吧。"  # noqa: RUF001
        return replace(response, evidence=replace(response.evidence, transcript=text),
                       raw_payload={"text": text, "synthetic": True})


# This standalone fixture application never reaches a paid perception provider.
patch("benma_api.api.routes.build_perception_provider", return_value=ExamplePerception()).start()

scratch = TemporaryDirectory(prefix="benma-web-smoke-")
root = Path(scratch.name)
settings = Settings(
    _env_file=None,
    environment="development",
    database_url=f"sqlite:///{root / 'smoke.db'}",
    audio_storage_dir=root / "audio",
    dev_auth_enabled=True,
    perception_provider="replay",
    assessment_provider="replay",
    reference_speech_provider="replay",
    alignment_provider="replay",
    acoustic_provider="praat",
)
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
sessions = sessionmaker(bind=engine, expire_on_commit=False)
store = LocalFilesystemAudioStore(settings.audio_storage_dir)
app = create_app(settings)


async def database():
    with sessions() as db:
        yield db


async def request_settings():
    return settings


async def audio_store():
    return store


async def interpreter():
    return SequencedInterpreter(["preserve"])


async def generator():
    return SequencedGenerator(["我们一起练习中文。"])


async def speech():
    return RecordingSpeechProvider()


app.dependency_overrides.update({
    get_db: database,
    get_request_settings: request_settings,
    get_audio_store: audio_store,
    get_contextual_interpreter: interpreter,
    get_assistant_response_generator: generator,
    get_assistant_speech_provider: speech,
})


# Gates are exclusive to this isolated unpaid browser fixture, never production.
_gates = {branch: asyncio.Event() for branch in ("analysis", "reply")}
for _gate in _gates.values():
    _gate.set()


@app.post("/__smoke/gates/{branch}/{action}")
async def gate(branch: str, action: str):
    event = _gates[branch]
    if action == "hold":
        event.clear()
    else:
        event.set()
    return {"ok": True}


@app.middleware("http")
async def control_arrival(request, call_next):
    if request.url.path.endswith("/speech-analysis"):
        await _gates["analysis"].wait()
    elif request.url.path.endswith("/user-turns/stream"):
        await _gates["reply"].wait()
    return await call_next(request)

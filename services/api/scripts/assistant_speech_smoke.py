"""Live Azure smoke for persisted conversational assistant speech."""

from __future__ import annotations

import io
import json
import tempfile
import uuid
import wave
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from benma_api.assistant_speech.factory import build_assistant_speech_provider
from benma_api.assistant_speech.repository import SqlAssistantSpeechRepository
from benma_api.assistant_speech.service import AssistantSpeechService
from benma_api.config import Settings
from benma_api.db.base import Base
from benma_api.db.models import (
    Account,
    AssistantGenerationRun,
    AssistantSpeechRun,
    AudioAsset,
    Conversation,
    ConversationTurn,
)
from benma_api.storage.audio_store import LocalFilesystemAudioStore

TEXTS = (
    "好呀，你想买什么水果？",
    "你是想说什么？",
    "可以啊，早点休息吧。",
)


def _generation(
    db: Session,
    *,
    account_id: uuid.UUID,
    conversation_id: uuid.UUID,
    text: str,
    sequence_number: int,
) -> AssistantGenerationRun:
    run = AssistantGenerationRun(
        account_id=account_id,
        conversation_id=conversation_id,
        triggering_user_turn_id=uuid.uuid4(),
        provider="smoke_fixture",
        product="persisted_text_fixture",
        adapter_version="1",
        model="fixed-smoke-text",
        generator_version="assistant-speech-smoke-v1",
        generator_configuration={"model": "fixed-smoke-text"},
        generation_type="clarification" if sequence_number == 2 else "reply",
        input_snapshot={"source": "assistant_speech_smoke"},
        generated_text=text,
        normalized_result={"generated_text": text},
        status="succeeded",
    )
    db.add(run)
    db.flush()
    db.add(
        ConversationTurn(
            account_id=account_id,
            conversation_id=conversation_id,
            sequence_number=sequence_number,
            role="assistant",
            assistant_text=text,
            assistant_generation_run_id=run.id,
        )
    )
    db.commit()
    return run


def main() -> int:
    try:
        settings = Settings(assistant_speech_provider="azure")
    except ValidationError as exc:
        print("BLOCKED_EXTERNAL: Azure assistant speech configuration unavailable")
        print(str(exc).splitlines()[0])
        return 2
    provider = build_assistant_speech_provider(settings)
    with tempfile.TemporaryDirectory(prefix="benma-assistant-speech-") as temp_dir:
        store = LocalFilesystemAudioStore(Path(temp_dir) / "audio")
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        results: list[dict[str, object]] = []
        with Session(engine, expire_on_commit=False) as db:
            account = Account()
            db.add(account)
            db.flush()
            conversation = Conversation(account_id=account.id)
            db.add(conversation)
            db.commit()
            for index, text in enumerate(TEXTS, start=1):
                generation = _generation(
                    db,
                    account_id=account.id,
                    conversation_id=conversation.id,
                    text=text,
                    sequence_number=index,
                )
                speech = AssistantSpeechService(
                    SqlAssistantSpeechRepository(db), store, settings
                ).run(
                    account_id=account.id,
                    assistant_generation_run_id=generation.id,
                    provider=provider,
                )
                if speech.status != "succeeded":
                    print(
                        json.dumps(
                            {
                                "status": speech.status,
                                "text_snapshot": speech.text_snapshot,
                                "provider": speech.provider,
                                "error_code": speech.error_code,
                                "error_message": speech.error_message,
                            },
                            ensure_ascii=False,
                            indent=2,
                        )
                    )
                    return 1
                assert speech.text_snapshot == generation.generated_text == text
                assert speech.audio_asset_id is not None
                audio_asset = speech.audio_asset_id
                persisted = db.get(AssistantSpeechRun, speech.id)
                assert persisted is not None and persisted.text_snapshot == text
                audio = db.get(AudioAsset, audio_asset)
                assert audio is not None
                payload = store.read(audio.storage_key)
                with wave.open(io.BytesIO(payload), "rb") as reader:
                    audio_format = {
                        "channels": reader.getnchannels(),
                        "sample_rate_hz": reader.getframerate(),
                        "sample_width_bits": reader.getsampwidth() * 8,
                        "frames": reader.getnframes(),
                    }
                results.append(
                    {
                        "text_snapshot": speech.text_snapshot,
                        "status": speech.status,
                        "provider": speech.provider,
                        "provider_version": speech.provider_version,
                        "voice": speech.voice,
                        "locale": speech.locale,
                        "mime_type": audio.mime_type,
                        "size_bytes": audio.size_bytes,
                        "sha256": audio.sha256,
                        "audio_format": audio_format,
                    }
                )
            assert len(list(db.scalars(select(AssistantSpeechRun)))) == len(TEXTS)
        engine.dispose()
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Append-only conversational speech derived from persisted assistant text."""

from __future__ import annotations

import time
import uuid
from contextlib import suppress
from copy import deepcopy

from benma_api.assistant_speech.repository import AssistantSpeechRepository
from benma_api.audio.service import inspect_audio, sha256_bytes
from benma_api.config import Settings
from benma_api.db.models import AssistantSpeechRun, AudioAsset
from benma_api.errors import AuthorizationError, BenmaError
from benma_api.speech.synthesis import SpeechSynthesisPort, SpeechSynthesisRequest
from benma_api.storage.audio_store import AudioObjectStore


class AssistantSpeechService:
    def __init__(
        self,
        repository: AssistantSpeechRepository,
        store: AudioObjectStore,
        settings: Settings,
    ) -> None:
        self.repository = repository
        self.store = store
        self.settings = settings

    def run(
        self,
        *,
        account_id: uuid.UUID,
        assistant_generation_run_id: uuid.UUID,
        provider: SpeechSynthesisPort,
    ) -> AssistantSpeechRun:
        """Render exactly one persisted generation; every call appends evidence."""
        source = self.repository.load_source(account_id, assistant_generation_run_id)
        if source is None:
            raise AuthorizationError("assistant generation run was not found")
        generation, assistant_turn = source
        text = generation.generated_text
        if text is None or not text.strip():
            raise RuntimeError("succeeded assistant generation has no text")

        configuration: dict[str, object] = {
            "model": self.settings.assistant_speech_model_version,
            "voice": self.settings.assistant_speech_voice,
            "locale": self.settings.assistant_speech_locale,
            "rate": self.settings.assistant_speech_rate,
            "output_format": "riff-24khz-16bit-mono-pcm",
            "timeout_seconds": self.settings.assistant_speech_timeout_seconds,
            "text_source": "assistant_generation_run.generated_text",
        }
        request = SpeechSynthesisRequest(
            text=text,
            locale=self.settings.assistant_speech_locale,
            voice=self.settings.assistant_speech_voice,
            model_version=self.settings.assistant_speech_model_version,
            rate=self.settings.assistant_speech_rate,
            timeout_seconds=self.settings.assistant_speech_timeout_seconds,
        )
        started = time.perf_counter()
        storage_key: str | None = None
        try:
            response = provider.synthesize(request)
            storage_key = f"{account_id}/assistant/{uuid.uuid4().hex}.wav"
            self.store.put(storage_key, response.audio)
            metadata = inspect_audio(
                self.store.path_for_processing(storage_key), self.settings
            )
        except BenmaError as exc:
            self._remove_failed_object(storage_key)
            return self._persist_failure(
                account_id=account_id,
                conversation_id=generation.conversation_id,
                assistant_generation_run_id=generation.id,
                assistant_turn_id=assistant_turn.id,
                provider=provider,
                configuration=configuration,
                text=text,
                latency_ms=round((time.perf_counter() - started) * 1000),
                error_code=exc.code,
                error_message=exc.message,
            )
        except Exception:
            self._remove_failed_object(storage_key)
            return self._persist_failure(
                account_id=account_id,
                conversation_id=generation.conversation_id,
                assistant_generation_run_id=generation.id,
                assistant_turn_id=assistant_turn.id,
                provider=provider,
                configuration=configuration,
                text=text,
                latency_ms=round((time.perf_counter() - started) * 1000),
                error_code="assistant_speech_failed",
                error_message="assistant speech generation failed",
            )

        assert storage_key is not None
        audio = AudioAsset(
            id=uuid.uuid4(),
            account_id=account_id,
            storage_key=storage_key,
            kind="assistant_speech",
            mime_type=response.mime_type,
            sha256=sha256_bytes(response.audio),
            size_bytes=len(response.audio),
            sample_rate_hz=metadata.sample_rate_hz,
            channels=metadata.channels,
            sample_width_bits=metadata.sample_width_bits,
            duration_seconds=metadata.duration_seconds,
        )
        run = AssistantSpeechRun(
            account_id=account_id,
            conversation_id=generation.conversation_id,
            assistant_generation_run_id=generation.id,
            assistant_turn_id=assistant_turn.id,
            audio_asset_id=audio.id,
            provider=provider.provider_name,
            product=provider.product_name,
            provider_version=response.provider_version,
            adapter_version=provider.adapter_version,
            model=self.settings.assistant_speech_model_version,
            voice=self.settings.assistant_speech_voice,
            locale=self.settings.assistant_speech_locale,
            generation_configuration={
                **deepcopy(configuration),
                "evidence_status": response.evidence_status,
            },
            text_snapshot=text,
            latency_ms=round((time.perf_counter() - started) * 1000),
            status="succeeded",
        )
        self.repository.add_audio(audio)
        self.repository.flush()
        self.repository.add_run(run)
        self.repository.commit()
        return run

    def _persist_failure(
        self,
        *,
        account_id: uuid.UUID,
        conversation_id: uuid.UUID,
        assistant_generation_run_id: uuid.UUID,
        assistant_turn_id: uuid.UUID,
        provider: SpeechSynthesisPort,
        configuration: dict[str, object],
        text: str,
        latency_ms: int,
        error_code: str,
        error_message: str,
    ) -> AssistantSpeechRun:
        run = AssistantSpeechRun(
            account_id=account_id,
            conversation_id=conversation_id,
            assistant_generation_run_id=assistant_generation_run_id,
            assistant_turn_id=assistant_turn_id,
            provider=provider.provider_name,
            product=provider.product_name,
            adapter_version=provider.adapter_version,
            model=self.settings.assistant_speech_model_version,
            voice=self.settings.assistant_speech_voice,
            locale=self.settings.assistant_speech_locale,
            generation_configuration=deepcopy(configuration),
            text_snapshot=text,
            latency_ms=latency_ms,
            status="failed",
            error_code=error_code,
            error_message=error_message,
        )
        self.repository.add_run(run)
        self.repository.commit()
        return run

    def _remove_failed_object(self, storage_key: str | None) -> None:
        if storage_key is None:
            return
        with suppress(OSError):
            self.store.delete(storage_key)

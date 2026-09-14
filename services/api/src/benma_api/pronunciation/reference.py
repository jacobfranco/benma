"""Replaceable reference-speech port, Azure adapter, and persisted cache."""

from __future__ import annotations

import hashlib
import io
import json
import math
import struct
import unicodedata
import uuid
import wave

from sqlalchemy import select
from sqlalchemy.orm import Session

from benma_api.audio.service import inspect_audio, sha256_bytes
from benma_api.config import Settings
from benma_api.db.models import AudioAsset, PronunciationTarget, ReferenceSpeechAsset
from benma_api.errors import AuthorizationError, BenmaError
from benma_api.pronunciation.acoustics import AutocorrelationAcousticAnalyzer
from benma_api.pronunciation.service import target_snapshot
from benma_api.speech.synthesis import (
    AzureSpeechSynthesisProvider,
    DisabledSpeechSynthesisProvider,
    SpeechSynthesisPort,
    SpeechSynthesisRequest,
    SpeechSynthesisResponse,
)
from benma_api.storage.audio_store import AudioObjectStore

# Compatibility names keep the pronunciation-facing API stable while the implementation is
# shared with conversational speech.
ReferenceSpeechRequest = SpeechSynthesisRequest
ReferenceSpeechResponse = SpeechSynthesisResponse
ReferenceSpeechPort = SpeechSynthesisPort
AzureReferenceSpeechProvider = AzureSpeechSynthesisProvider


def _synthetic_reference_wav(tones: list[int | None]) -> bytes:
    """Audible CI/development fixture; deliberately not speech or imitation material."""

    sample_rate = 16000
    frames: list[int] = []
    patterns = {
        0: (180.0, 170.0),
        1: (240.0, 240.0),
        2: (160.0, 260.0),
        3: (210.0, 140.0),
        4: (270.0, 140.0),
        None: (190.0, 190.0),
    }
    for tone in tones or [None]:
        start, end = patterns[tone]
        count = round(sample_rate * 0.32)
        phase = 0.0
        for index in range(count):
            frequency = start + (end - start) * index / max(1, count - 1)
            phase += 2 * math.pi * frequency / sample_rate
            envelope = min(1.0, index / 160, (count - index) / 160)
            frames.append(round(math.sin(phase) * envelope * 5000))
        frames.extend([0] * round(sample_rate * 0.06))
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(sample_rate)
        writer.writeframes(struct.pack(f"<{len(frames)}h", *frames))
    return output.getvalue()


class ReplayReferenceSpeechProvider:
    provider_name = "replay"
    product_name = "synthetic_reference_speech"
    adapter_version = "1.0.0"

    def __init__(self, tones: list[int | None]) -> None:
        self.tones = tones

    def synthesize(self, request: ReferenceSpeechRequest) -> ReferenceSpeechResponse:
        del request
        return ReferenceSpeechResponse(
            audio=_synthetic_reference_wav(self.tones),
            mime_type="audio/wav",
            provider_version="synthetic-tone-fixture-v1",
            evidence_status="synthetic_replay",
        )


def build_reference_provider(
    settings: Settings, target: PronunciationTarget
) -> ReferenceSpeechPort:
    if settings.reference_speech_provider == "replay":
        return ReplayReferenceSpeechProvider(target.lexical_tones)
    if settings.reference_speech_provider == "azure":
        assert settings.azure_speech_key is not None
        assert settings.azure_speech_region is not None
        return AzureSpeechSynthesisProvider(
            settings.azure_speech_key.get_secret_value(), settings.azure_speech_region
        )
    return DisabledSpeechSynthesisProvider()


def _cache_key(target: PronunciationTarget, settings: Settings, provider: str) -> str:
    payload = {
        "text": unicodedata.normalize("NFKC", target.text).strip(),
        "locale": "zh-CN",
        "voice": settings.reference_speech_voice,
        "provider": provider,
        "model_version": settings.reference_speech_model_version,
        "rate": settings.reference_speech_rate,
        "output": "pcm-wav",
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


class ReferenceSpeechService:
    def __init__(self, db: Session, store: AudioObjectStore, settings: Settings) -> None:
        self.db = db
        self.store = store
        self.settings = settings

    def get_or_create(
        self,
        *,
        account_id: uuid.UUID,
        target_id: uuid.UUID,
        force: bool = False,
        timeout_seconds: float = 30.0,
    ) -> ReferenceSpeechAsset:
        target = self.db.get(PronunciationTarget, target_id)
        if target is None or target.account_id != account_id:
            raise AuthorizationError("pronunciation target was not found")
        provider = build_reference_provider(self.settings, target)
        cache_key = _cache_key(target, self.settings, provider.provider_name)
        if not force:
            cached = self.db.scalar(
                select(ReferenceSpeechAsset)
                .where(
                    ReferenceSpeechAsset.account_id == account_id,
                    ReferenceSpeechAsset.cache_key == cache_key,
                    ReferenceSpeechAsset.status == "succeeded",
                )
                .order_by(ReferenceSpeechAsset.created_at.desc())
            )
            if cached is not None:
                return cached
        config = {
            "rate": self.settings.reference_speech_rate,
            "output_format": "pcm-wav",
            "evidence_role": "example_not_grading_truth",
        }
        request = ReferenceSpeechRequest(
            text=target.text,
            locale="zh-CN",
            voice=self.settings.reference_speech_voice,
            model_version=self.settings.reference_speech_model_version,
            rate=self.settings.reference_speech_rate,
            timeout_seconds=timeout_seconds,
        )
        snapshot = target_snapshot(target)
        try:
            response = provider.synthesize(request)
            key = f"{account_id}/reference/{uuid.uuid4().hex}.wav"
            self.store.put(key, response.audio)
            metadata = inspect_audio(self.store.path_for_processing(key), self.settings)
            reference_acoustics = AutocorrelationAcousticAnalyzer().analyze(
                self.store.path_for_processing(key)
            )
            audio = AudioAsset(
                account_id=account_id,
                storage_key=key,
                kind="reference",
                mime_type=response.mime_type,
                sha256=sha256_bytes(response.audio),
                size_bytes=len(response.audio),
                sample_rate_hz=metadata.sample_rate_hz,
                channels=metadata.channels,
                sample_width_bits=metadata.sample_width_bits,
                duration_seconds=metadata.duration_seconds,
            )
            self.db.add(audio)
            self.db.flush()
            asset = ReferenceSpeechAsset(
                account_id=account_id,
                target_id=target_id,
                audio_asset_id=audio.id,
                cache_key=cache_key,
                provider=provider.provider_name,
                voice=self.settings.reference_speech_voice,
                locale="zh-CN",
                model_version=response.provider_version,
                generation_config={**config, "evidence_status": response.evidence_status},
                target_snapshot=snapshot,
                acoustic_result=reference_acoustics,
                status="succeeded",
            )
            self.db.add(asset)
            self.db.commit()
            return asset
        except BenmaError as exc:
            asset = ReferenceSpeechAsset(
                account_id=account_id,
                target_id=target_id,
                cache_key=cache_key,
                provider=provider.provider_name,
                voice=self.settings.reference_speech_voice,
                locale="zh-CN",
                model_version=self.settings.reference_speech_model_version,
                generation_config=config,
                target_snapshot=snapshot,
                status="failed",
                error_code=exc.code,
                error_message=exc.message,
            )
            self.db.add(asset)
            self.db.commit()
            return asset

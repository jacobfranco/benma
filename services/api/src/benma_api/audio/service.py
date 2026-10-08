"""Original-preserving audio validation and canonical ingest."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from benma_api.audio.presence import require_speech
from benma_api.config import Settings
from benma_api.db.models import AudioAsset, PracticeSession, Utterance
from benma_api.errors import AuthorizationError, InvalidAudioError
from benma_api.storage.audio_store import AudioObjectStore

MIME_EXTENSIONS = {
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
    "audio/flac": ".flac",
}


@dataclass(frozen=True, slots=True)
class AudioMetadata:
    sample_rate_hz: int | None
    channels: int | None
    sample_width_bits: int | None
    duration_seconds: float


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inspect_audio(path: Path, settings: Settings) -> AudioMetadata:
    try:
        completed = subprocess.run(
            [
                settings.ffprobe_binary,
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=sample_rate,channels,bits_per_sample:format=duration",
                "-of",
                "json",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
        payload = json.loads(completed.stdout)
        stream = payload["streams"][0]
        duration = float(payload["format"]["duration"])
    except (
        OSError,
        subprocess.SubprocessError,
        ValueError,
        KeyError,
        IndexError,
        json.JSONDecodeError,
    ) as exc:
        raise InvalidAudioError("audio is corrupt or uses an unsupported container") from exc
    if duration <= 0:
        raise InvalidAudioError("audio duration must be greater than zero")
    return AudioMetadata(
        sample_rate_hz=int(stream["sample_rate"]) if stream.get("sample_rate") else None,
        channels=int(stream["channels"]) if stream.get("channels") else None,
        sample_width_bits=(
            int(stream["bits_per_sample"]) if stream.get("bits_per_sample") else None
        ),
        duration_seconds=duration,
    )


def canonicalize(source: Path, settings: Settings) -> bytes:
    with tempfile.TemporaryDirectory(prefix="benma-canonical-") as directory:
        output = Path(directory) / "canonical.wav"
        try:
            subprocess.run(
                [
                    settings.ffmpeg_binary,
                    "-v",
                    "error",
                    "-nostdin",
                    "-i",
                    str(source),
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-c:a",
                    "pcm_s16le",
                    str(output),
                ],
                check=True,
                capture_output=True,
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise InvalidAudioError("audio could not be canonicalized") from exc
        return output.read_bytes()


class AudioIngestService:
    def __init__(self, db: Session, store: AudioObjectStore, settings: Settings) -> None:
        self.db = db
        self.store = store
        self.settings = settings

    def ingest(
        self,
        *,
        account_id: uuid.UUID,
        data: bytes,
        mime_type: str,
        practice_session_id: uuid.UUID | None,
    ) -> Utterance:
        if not data:
            raise InvalidAudioError("audio upload is empty")
        if len(data) > self.settings.max_upload_bytes:
            raise InvalidAudioError("audio upload exceeds the configured size limit")
        # MediaRecorder includes codec parameters (e.g. audio/webm;codecs=opus).
        # Keep the same media-type allowlist and inspect the actual container below.
        mime_type = mime_type.split(";", 1)[0].strip().casefold()
        extension = MIME_EXTENSIONS.get(mime_type)
        if extension is None:
            raise InvalidAudioError("audio MIME type is not permitted")
        if practice_session_id is not None:
            practice = self.db.get(PracticeSession, practice_session_id)
            if practice is None or practice.account_id != account_id:
                raise AuthorizationError("practice session was not found")

        original_key = f"{account_id}/original/{uuid.uuid4().hex}{extension}"
        self.store.put(original_key, data)
        try:
            original_meta = inspect_audio(
                self.store.path_for_processing(original_key), self.settings
            )
        except InvalidAudioError:
            self.store.delete(original_key)
            raise
        if original_meta.duration_seconds > self.settings.max_audio_duration_seconds:
            self.store.delete(original_key)
            raise InvalidAudioError("audio duration exceeds the configured limit")

        original = AudioAsset(
            account_id=account_id,
            storage_key=original_key,
            kind="original",
            mime_type=mime_type,
            sha256=sha256_bytes(data),
            size_bytes=len(data),
            sample_rate_hz=original_meta.sample_rate_hz,
            channels=original_meta.channels,
            sample_width_bits=original_meta.sample_width_bits,
            duration_seconds=original_meta.duration_seconds,
        )
        self.db.add(original)
        self.db.commit()  # original evidence survives every later failure

        canonical_key = f"{account_id}/canonical/{uuid.uuid4().hex}.wav"
        try:
            canonical_data = canonicalize(
                self.store.path_for_processing(original_key), self.settings
            )
            require_speech(canonical_data)
            self.store.put(canonical_key, canonical_data)
            canonical_meta = inspect_audio(
                self.store.path_for_processing(canonical_key), self.settings
            )
            canonical = AudioAsset(
                account_id=account_id,
                storage_key=canonical_key,
                kind="canonical",
                mime_type="audio/wav",
                sha256=sha256_bytes(canonical_data),
                size_bytes=len(canonical_data),
                sample_rate_hz=canonical_meta.sample_rate_hz,
                channels=canonical_meta.channels,
                sample_width_bits=16,
                duration_seconds=canonical_meta.duration_seconds,
                source_asset_id=original.id,
            )
            utterance = Utterance(
                account_id=account_id,
                practice_session_id=practice_session_id,
                original_audio_asset_id=original.id,
                canonical_audio_asset_id=canonical.id,
                original_audio=original,
                canonical_audio=canonical,
            )
            self.db.add_all((canonical, utterance))
            self.db.commit()
            return utterance
        except Exception:
            self.db.rollback()
            self.store.delete(canonical_key)
            raise

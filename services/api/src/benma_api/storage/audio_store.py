"""Storage-key-only audio object store contract and local implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from benma_api.config import get_settings


class AudioObjectStore(Protocol):
    def put(self, key: str, data: bytes) -> None: ...
    def read(self, key: str) -> bytes: ...
    def path_for_processing(self, key: str) -> Path: ...
    def delete(self, key: str) -> None: ...


class LocalFilesystemAudioStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        if not key or key.startswith(("/", "\\")) or ".." in Path(key).parts:
            raise ValueError("invalid storage key")
        candidate = (self.root / key).resolve()
        if not candidate.is_relative_to(self.root):
            raise ValueError("storage key escapes object store")
        return candidate

    def put(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        exclusive = path.open("xb")
        with exclusive:
            exclusive.write(data)

    def read(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def path_for_processing(self, key: str) -> Path:
        return self._path(key)

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)


async def get_audio_store() -> AudioObjectStore:
    return LocalFilesystemAudioStore(get_settings().audio_storage_dir)

"""Original-preserving import, capture, and canonical PCM WAV normalization."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

from benchmark.models import AudioAsset


@dataclass(frozen=True)
class WavInfo:
    sample_rate_hz: int
    channels: int
    sample_width_bits: int
    frames: int
    duration_seconds: float


def inspect_wav(path: Path) -> WavInfo:
    with wave.open(str(path), "rb") as stream:
        frames = stream.getnframes()
        rate = stream.getframerate()
        return WavInfo(
            sample_rate_hz=rate,
            channels=stream.getnchannels(),
            sample_width_bits=stream.getsampwidth() * 8,
            frames=frames,
            duration_seconds=frames / rate if rate else 0.0,
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_to_canonical(source: Path, destination: Path) -> WavInfo:
    """Generate mono 16 kHz 16-bit PCM without modifying ``source``."""
    if not source.is_file() or source.stat().st_size == 0:
        raise ValueError(f"audio source is missing or empty: {source}")
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required for canonical audio generation")
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-map_metadata",
            "-1",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(destination),
        ],
        check=True,
        capture_output=True,
    )
    info = inspect_wav(destination)
    if (info.sample_rate_hz, info.channels, info.sample_width_bits) != (16000, 1, 16):
        raise RuntimeError("ffmpeg did not produce canonical 16 kHz mono PCM16")
    if info.frames == 0:
        raise ValueError("canonical audio is empty")
    return info


def import_recording(
    source: Path,
    *,
    sample_id: str,
    recordings_root: Path,
) -> AudioAsset:
    """Preserve the source bytes and generate a distinct canonical asset."""
    original_suffix = source.suffix.lower() or ".bin"
    original = recordings_root / "original" / f"{sample_id}{original_suffix}"
    canonical = recordings_root / "canonical" / f"{sample_id}.wav"
    original.parent.mkdir(parents=True, exist_ok=True)
    if original.exists():
        raise FileExistsError(f"original recording already exists: {original}")
    shutil.copy2(source, original)
    try:
        info = normalize_to_canonical(original, canonical)
    except BaseException:
        original.unlink(missing_ok=True)
        canonical.unlink(missing_ok=True)
        raise
    return AudioAsset(
        asset_path=canonical,
        original_asset_path=original,
        sha256=sha256_file(canonical),
        media_type="audio/wav",
        sample_rate_hz=info.sample_rate_hz,
        channels=info.channels,
        sample_width_bits=info.sample_width_bits,
        duration_seconds=info.duration_seconds,
    )


def capture_with_ffmpeg(
    destination: Path,
    *,
    input_format: str,
    input_device: str,
    duration_seconds: float | None = None,
) -> None:
    """Capture original audio using an explicit ffmpeg input format/device."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required for recording")
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-f", input_format]
    command.extend(["-i", input_device])
    if duration_seconds is not None:
        command.extend(["-t", str(duration_seconds)])
    command.extend(["-c:a", "pcm_s24le", str(destination)])
    subprocess.run(command, check=True)


def play_audio(path: Path) -> None:
    player = shutil.which("ffplay")
    if player is None:
        raise RuntimeError("ffplay is required for playback")
    subprocess.run([player, "-nodisp", "-autoexit", "-loglevel", "error", str(path)], check=True)

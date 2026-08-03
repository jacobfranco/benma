from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

import pytest

from benchmark.models import AudioAsset, BenchmarkSample, SpeakerCategory


def write_wav(
    path: Path,
    *,
    rate: int = 16000,
    duration: float = 0.5,
    frequency: float = 200.0,
    channels: int = 1,
    amplitude: float = 0.4,
) -> Path:
    frames = round(rate * duration)
    values: list[int] = []
    for index in range(frames):
        sample = round(32767 * amplitude * math.sin(2 * math.pi * frequency * index / rate))
        values.extend([sample] * channels)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(channels)
        stream.setsampwidth(2)
        stream.setframerate(rate)
        stream.writeframes(struct.pack(f"<{len(values)}h", *values))
    return path


@pytest.fixture
def canonical_wav(tmp_path: Path) -> Path:
    return write_wav(tmp_path / "tone.wav")


@pytest.fixture
def recorded_sample(canonical_wav: Path) -> BenchmarkSample:
    return BenchmarkSample(
        sample_id="test_sample",
        corpus_version="test",
        audio=AudioAsset(
            asset_path=canonical_wav,
            sample_rate_hz=16000,
            channels=1,
            sample_width_bits=16,
            duration_seconds=0.5,
        ),
        speaker_category=SpeakerCategory.LEARNER,
        intended_text="你好",
        intended_pinyin=("nǐ", "hǎo"),
        lexical_tones=(3, 3),
        expected_surface_tones=("T2-sandhi", "T3"),
        status="recorded",
    )

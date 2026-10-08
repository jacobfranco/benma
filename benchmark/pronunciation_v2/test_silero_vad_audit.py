"""Opt-in by invoking this file: real local model/corpus, no downloads/skips."""

from __future__ import annotations

import inspect
import io
import json
import math
import wave

import numpy as np
import pytest
from silero_vad_audit import (
    PRIOR,
    RATE,
    REPORT,
    THRESHOLDS,
    WINDOW,
    AudioOnlySilero,
    NumpySilero,
    corpus,
    normalize_audio,
    read_frozen_audio,
    segment,
)

IDS = [e["id"] for e in json.loads((PRIOR / "corpus.json").read_text())["entries"]]


@pytest.fixture(scope="module")
def verified():
    return corpus()


@pytest.fixture(scope="module")
def adapter(verified):
    return AudioOnlySilero()


@pytest.fixture(scope="module")
def numpy_adapter(verified):
    return NumpySilero()


def saved(identity):
    return json.loads((REPORT / "probabilities" / f"{identity}.json").read_text())


def test_exact_frozen_coverage_and_no_skipped_artifacts(verified):
    manifest, entries, _ = verified
    assert (REPORT / "corpus.json").read_bytes() == manifest
    assert {p.stem for p in (REPORT / "probabilities").glob("*.json")} == set(entries)
    for filename in ("default-results.json", "baseline-replay.json"):
        rows = json.loads((REPORT / filename).read_text())["rows"]
        assert [r["id"] for r in rows] == IDS
    sweep = json.loads((REPORT / "threshold-results.json").read_text())
    assert tuple(run["threshold"] for run in sweep["runs"]) == THRESHOLDS
    for run in sweep["runs"]:
        assert [r["id"] for r in run["rows"]] == IDS


@pytest.mark.parametrize("identity", IDS)
def test_determinism_raw_preservation_and_upstream_parity(
    identity, verified, adapter, numpy_adapter
):
    _, entries, audio = verified
    baseline = saved(identity)
    first = adapter.infer(audio[identity])
    # Different intervening utterance must not leak recurrent state/context.
    adapter.infer(audio["silence_periodic"])
    assert adapter.infer(audio[identity]) == first
    assert numpy_adapter.infer(audio[identity]) == first
    assert first["frames"] == baseline["frames"]
    assert baseline["audio_sha256"] == entries[identity]["sha256"]
    assert len(first["frames"]) == math.ceil(first["normalized_samples"] / WINDOW)
    for index, frame in enumerate(first["frames"]):
        assert frame["start_sample"] == index * WINDOW
        assert frame["end_sample"] == min((index + 1) * WINDOW, first["normalized_samples"])
        assert frame["start_seconds"] == frame["start_sample"] / RATE
        assert frame["end_seconds"] == frame["end_sample"] / RATE
        assert 0 <= frame["probability"] <= 1
    samples, _ = normalize_audio(audio[identity])
    direct = adapter.helpers.get_speech_timestamps(
        adapter.helpers.torch.from_numpy(samples), adapter.model, sampling_rate=RATE
    )
    assert direct == segment(baseline, adapter.helpers)["regions_samples"]


@pytest.mark.parametrize("identity", IDS)
def test_transcript_and_target_invariance(identity, verified, adapter):
    data = verified[2][identity]
    variants = [
        {"transcript": "我要一个苹果", "target": "我要一个苹果"},
        {"transcript": "噗咕啦 blorf zhak", "target": "我要一个苹果"},
        {"transcript": "This is non-Chinese speech", "target": "我要一个苹果"},
        {"transcript": "", "target": "我要一个苹果"},
        {"transcript": None, "target": None},
        {"transcript": "我要一个苹果", "target": "完全不同的目标"},
    ]
    # Metadata lives in the test record only: the call boundary accepts bytes.
    expected = saved(identity)
    expected_regions = segment(expected, adapter.helpers)["regions_samples"]
    for metadata in variants:
        associated_record = {"audio": data, **metadata}
        actual = adapter.infer(associated_record["audio"])
        assert actual["frames"] == expected["frames"]
        assert segment(actual, adapter.helpers)["regions_samples"] == expected_regions


def test_text_cannot_enter_either_adapter(adapter, numpy_adapter, verified):
    for instance in (adapter, numpy_adapter):
        assert list(inspect.signature(instance.infer).parameters) == ["pcm"]
        for forbidden in ("transcript", "target", "language", "pinyin"):
            with pytest.raises(TypeError):
                instance.infer(verified[2]["human_control"], **{forbidden: "text"})


def wav(values, rate):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(rate)
        stream.writeframes(np.asarray(values, dtype="<i2").tobytes())
    return buffer.getvalue()


@pytest.mark.parametrize("rate", [8000, 16000, 24000, 44100, 48000])
def test_sample_rate_normalization_and_tail_coverage(rate, adapter):
    # Numerical unit fixture only; never added to the frozen evaluation corpus.
    duration = 0.113
    values = np.rint(10000 * np.sin(2 * np.pi * 440 * np.arange(round(rate * duration)) / rate))
    data = wav(values, rate)
    samples, meta = normalize_audio(data)
    assert meta["input_sample_rate"] == rate
    assert meta["normalized_sample_rate"] == RATE
    assert len(samples) == math.ceil(len(values) * RATE / rate)
    if rate == RATE:
        np.testing.assert_array_equal(samples, values.astype(np.float32) / 32768)
    # Independent physical oracle: resampling preserves tone/time/amplitude.
    reference = 10000 / 32768 * np.sin(2 * np.pi * 440 * np.arange(len(samples)) / RATE)
    assert np.max(abs(samples[80:-80] - reference[80:-80])) < 0.001
    timeline = adapter.infer(data)
    assert timeline["frames"][-1]["end_sample"] == len(samples)
    assert timeline["last_chunk_zero_padding_samples"] == (-len(samples)) % WINDOW


def test_corrupt_audio_and_parent_hash_fail_closed(verified):
    _, entries, _ = verified
    entry = dict(entries["human_control"], sha256="0" * 64)
    with pytest.raises(ValueError, match="Audio hash mismatch"):
        read_frozen_audio(entry, entries)
    entry = dict(entries["short_human_a"], parent_sha256="0" * 64)
    with pytest.raises(ValueError, match="Parent hash mismatch"):
        read_frozen_audio(entry, entries)


def test_upstream_threshold_equality_hysteresis_and_padding(adapter):
    helper = adapter.helpers.get_speech_timestamps_from_probs
    # Start is >= threshold, despite the upstream docstring saying ABOVE.
    assert helper([0.5] * 10) == [{"start": 0, "end": 5120}]
    assert helper([0.499] * 10) == []
    # Exactly the exit threshold is not silence; below it starts a silence run.
    assert helper([0.5] * 10 + [0.35] * 5) == [{"start": 0, "end": 7680}]
    assert helper([0.5] * 10 + [0.349] * 5) == [{"start": 0, "end": 5600}]


def test_short_audio_is_not_extended_by_tail_padding(adapter):
    helper = adapter.helpers.get_speech_timestamps_from_probs
    # Tests the mandated default, not a duration-policy sweep.
    assert helper([0.99] * 4, audio_length_samples=1760) == []  # 110 ms
    assert helper([0.99] * 8, audio_length_samples=4000) == []  # exactly 250 ms
    assert helper([0.99] * 8, audio_length_samples=4096) == [{"start": 0, "end": 4096}]

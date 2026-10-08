"""Sanitized structural regressions; no recordings, credentials or provider requests."""

from __future__ import annotations

import copy
import math
import uuid
import wave
from unittest.mock import Mock

import numpy as np
import pytest
from sqlalchemy import select
from test_perceived_speech import perception_for

from benma_api.db.models import AudioAsset, PerceptionRun, PronunciationTarget
from benma_api.pronunciation.acoustics import PraatAcousticAnalyzer
from benma_api.pronunciation.alignment import AlignmentResponse
from benma_api.pronunciation.azure_alignment import azure_syllable_units, timing_payload
from benma_api.pronunciation.contours import classify_contour, display_contour
from benma_api.pronunciation.perceived import PerceivedSpeechAnalysisService, perceived_syllables
from benma_api.pronunciation.surface import surface_expectations
from benma_api.speech.providers.openai import language_metadata


def timing_fixture(text="你好", labels=("ni 2", "hao 3"), spans=((0.59, 1.17), (1.18, 1.71))):
    phones = [
        {
            "Phoneme": label,
            "Offset": round(a * 1e7),
            "Duration": round((b - a) * 1e7),
            "PronunciationAssessment": {"AccuracyScore": 100},
        }
        for label, (a, b) in zip(labels, spans, strict=True)
    ]
    return {
        "NBest": [
            {
                "Words": [
                    {
                        "Word": text,
                        "Offset": phones[0]["Offset"],
                        "Duration": round((spans[-1][1] - spans[0][0]) * 1e7),
                        "Phonemes": phones,
                        "PronunciationAssessment": {"AccuracyScore": 99, "ErrorType": "None"},
                    }
                ]
            }
        ]
    }


def test_azure_full_syllables_keep_offsets_and_ignore_reference_tone_and_scores():
    payload = timing_payload(timing_fixture())
    units = azure_syllable_units(payload, "你好。", ["nǐ", "hǎo"])
    assert [(u["start_seconds"], u["end_seconds"]) for u in units] == [(0.59, 1.17), (1.18, 1.71)]
    assert [u["label"] for u in units] == ["你", "好"]
    assert "Score" not in str(payload)
    payload["words"][0]["phones"] = []
    assert azure_syllable_units(payload, "你好", ["nǐ", "hǎo"]) == []
    assert azure_syllable_units(timing_payload(timing_fixture()), "你号", ["nǐ", "hào"]) == []


def test_azure_eleven_spans_are_provider_offsets_not_equal_splits():
    text = "你好今天我们聊聊周末吧"
    labels = (
        "ni 3",
        "hao 3",
        "jin 1",
        "tian 1",
        "wo 3",
        "men 5",
        "liao 2",
        "liao 2",
        "zhou 1",
        "mo 4",
        "ba 5",
    )
    spans = (
        (0.77, 1.22),
        (1.23, 1.59),
        (1.62, 1.89),
        (1.90, 2.27),
        (2.28, 2.48),
        (2.49, 3.12),
        (3.28, 3.91),
        (3.92, 4.29),
        (4.30, 4.44),
        (4.45, 4.55),
        (4.56, 4.94),
    )
    readings = [s.pinyin for s in perceived_syllables(text, {})]
    words = []
    for start, end in ((0, 2), (2, 4), (4, 6), (6, 8), (8, 10), (10, 11)):
        words.extend(
            timing_fixture(text[start:end], labels[start:end], spans[start:end])["NBest"][0][
                "Words"
            ]
        )
    units = azure_syllable_units(timing_payload({"NBest": [{"Words": words}]}), text, readings)
    assert [(u["start_seconds"], u["end_seconds"]) for u in units] == list(spans)
    assert len(units) == 11


@pytest.mark.parametrize(
    "text,lexical,surface",
    [
        ("你好", [3, 3], [2, 3]),
        ("不是", [4, 4], [2, 4]),
        ("一个", [1, 4], [2, None]),
        ("一天", [1, 1], [4, 1]),
        ("第一", [4, 1], [4, 1]),
        ("看一看", [None, 1, None], [None, None, None]),
        ("我很好", [3, 3, 3], [None, None, None]),
        ("我们", [3, 0], [3, 0]),
    ],
)
def test_surface_separate_from_dictionary(text, lexical, surface):
    syllables = perceived_syllables(text, {})
    assert [s.lexical_tone for s in syllables] == lexical
    assert [s.expected_surface_tone for s in syllables] == surface


@pytest.mark.parametrize(
    "raw,expected",
    [
        ({}, (None, None)),
        ({"languages": []}, (None, [])),
        ({"languages": [{"code": "zh"}]}, ("zh", [{"code": "zh"}])),
        ({"language": "Chinese"}, ("Chinese", None)),
        ({"languages": 42}, (None, None)),
    ],
)
def test_provider_language_is_not_fabricated(raw, expected):
    assert language_metadata(raw) == expected


def test_reduplication_surface_remains_unset_with_known_readings():
    assert [s.tone for s in surface_expectations("看一看", [0, 1, 2], [4, 1, 4])] == [4, None, 4]


def test_optional_warmup_initialization_cannot_block_perception(
    monkeypatch, session_factory, uploaded_utterance, store, settings
):
    from benma_api.db.models import Utterance
    from benma_api.pronunciation.warmup import start_acoustic_warmup

    def broken(_):
        raise ImportError("unavailable optional tracker")

    monkeypatch.setattr("benma_api.pronunciation.warmup.build_acoustic_analyzer", broken)
    with session_factory() as db:
        utterance = db.get(Utterance, uuid.UUID(str(uploaded_utterance["id"])))
        assert (
            start_acoustic_warmup(
                db, store, settings, account_id=utterance.account_id, utterance_id=utterance.id
            )
            is None
        )


@pytest.mark.parametrize(
    "shape,label",
    [
        ("level", "1-like"),
        ("rise", "2-like"),
        ("fall", "4-like"),
        ("dip", "3-like"),
        ("hum", "unclear"),
        ("low_voice", "1-like"),
        ("low_dip", "3-like"),
        ("high_voice", "1-like"),
    ],
)
def test_praat_synthetic_audio_and_quality_gate(tmp_path, shape, label):
    rate = 16000
    t = np.arange(rate) / rate
    movement = {
        "level": t * 0,
        "rise": t * 8,
        "fall": -t * 8,
        "dip": np.abs(t - 0.5) * 16 - 8,
        "hum": t * 0,
        "low_voice": t * 0,
        "low_dip": np.abs(t - 0.5) * 16 - 8,
        "high_voice": t * 0,
    }[shape]
    base = {"hum": 60, "low_voice": 55, "low_dip": 90, "high_voice": 300}.get(shape, 150)
    hz = base * 2 ** (movement / 12)
    phase = np.cumsum(hz) * (2 * math.pi / rate)
    samples = (
        np.sin(phase)
        if shape == "hum"
        else np.sin(phase) + 0.6 * np.sin(2 * phase) + 0.4 * np.sin(3 * phase)
    )
    path = tmp_path / "synthetic.wav"
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes((samples * 0.15 * 32767).astype("<i2").tobytes())
    result = PraatAcousticAnalyzer().analyze(path)
    raw = result["f0"]
    before = copy.deepcopy(raw)
    observed = classify_contour(display_contour(raw), 0.15, 0.85, raw=raw)
    assert observed.classification == label
    assert before == raw
    assert all("tracker_f0_hz" in p for p in raw)
    if shape == "hum":
        assert observed.reason == "low_frequency_contamination"
        assert any(p["tracker_f0_hz"] for p in raw)


def test_exact_perception_lineage_real_timing_and_mine(
    session_factory, uploaded_utterance, store, settings
):
    perception = perception_for(session_factory, uploaded_utterance, "你好。")
    raw = [
        {
            "timestamp_seconds": i / 100,
            "f0_hz": 140 * 2 ** ((i / 100) * 6 / 12),
            "voicing_probability": 0.99,
        }
        for i in range(200)
    ]
    analyzer = Mock(algorithm_name="fixture", algorithm_version="1", parameters={})
    analyzer.analyze.return_value = {"f0": raw, "mobile_f0": raw}
    payload = timing_payload(timing_fixture())
    aligner = Mock(
        algorithm_name="azure_speech_alignment_only",
        algorithm_version="test",
        configuration={"purpose": "alignment_only"},
    )
    aligner.align.return_value = AlignmentResponse(
        units=azure_syllable_units(payload, perception.transcript, ["nǐ", "hǎo"]),
        raw_result=payload,
        evidence_status="live_provider",
    )
    with session_factory() as db:
        asset = db.scalar(select(AudioAsset).where(AudioAsset.kind == "canonical"))
        asset.duration_seconds = 2
        db.commit()
        run = PerceivedSpeechAnalysisService(
            db, store, settings, analyzer=analyzer, aligner=aligner
        ).run(account_id=perception.account_id, perception_run_id=perception.id)
        assert run.alignment_reference_text == perception.transcript
        assert run.result["timing_coverage"] == 1
        evidence = run.result["timing_evidence"]
        assert evidence["perception_run_id"] == str(perception.id)
        assert evidence["reference_text"] == perception.transcript
        assert evidence["provider_timing"] == payload
        assert "score" not in str(run.result).lower()
        assert all(s["display_contour"]["segments"] for s in run.result["syllables"])
        assert all(
            s["observed_contour"]["classification"] == "unclear" for s in run.result["syllables"]
        )
        assert db.scalar(select(PronunciationTarget)) is None
        assert db.get(PerceptionRun, perception.id).raw_payload_json == {"immutable": True}
        assert aligner.align.call_args.args[0].reference_text == perception.transcript


def test_readings_are_owned_and_preserve_non_han(
    client, auth_header, uploaded_utterance, session_factory
):
    run = perception_for(session_factory, uploaded_utterance, "Neal 你好 Zaigan")
    path = f"/v1/perceptions/{run.id}/readings"
    data = client.get(path, headers=auth_header).json()
    assert [s["characters"] for s in data["syllables"]] == ["你", "好"]
    assert [s["text"] for s in data["unresolved_spans"]] == ["Neal", "Zaigan"]
    other = client.post("/v1/dev/auth", json={"phone_number": "+12025550188"}).json()
    assert (
        client.get(path, headers={"Authorization": f"Bearer {other['token']}"}).status_code == 404
    )

"""Frozen private audio replay; explicit expected failures keep blockers visible.

BENMA_PRESENCE_CORPUS=1 enables these local-only tests. No provider is called.
User-labelled negatives are never relabelled from ASR or candidate features.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import uuid
import wave
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy import func, select

from benma_api.api.routes import get_assistant_response_generator, get_contextual_interpreter
from benma_api.audio.presence import require_speech
from benma_api.db.models import (
    AudioAsset,
    ConversationTurn,
    PerceivedSpeechAnalysis,
    PerceptionRun,
    PronunciationAttempt,
    Utterance,
)
from benma_api.errors import NoSpeechError
from benma_api.pronunciation.pitch_evidence import (
    build_pitch_track,
    interpretation_eligibility,
    project_pitch,
)

ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / "docs/research/pronunciation-v2/2026-10-06-speech-presence"
CORPUS = json.loads((REPORT / "corpus.json").read_text())["entries"]
BY_ID = {r["id"]: r for r in CORPUS}
KNOWN_FALSE_ACCEPTS = {
    "silence_accidental",
    "neg_clicks",
    "padding_human_head",
    "padding_human_tail",
    "padding_low_voice",
    "padding_phone",
}
pytestmark = pytest.mark.skipif(
    os.getenv("BENMA_PRESENCE_CORPUS") != "1", reason="opt-in frozen private presence corpus"
)


def audio(identity):
    entry = BY_ID[identity]
    if "parent_id" in entry:
        parent = audio(entry["parent_id"])
        assert hashlib.sha256(parent).hexdigest() == entry["parent_sha256"]
        start, end = entry["interval_seconds"]
        with wave.open(io.BytesIO(parent)) as reader:
            rate = reader.getframerate()
            reader.setpos(round(start * rate))
            frames = reader.readframes(round((end - start) * rate))
        output = io.BytesIO()
        with wave.open(output, "wb") as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(rate)
            writer.writeframes(frames)
        data = output.getvalue()
    else:
        data = (ROOT / entry["path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == entry["sha256"]
    return data


def accepted(data, transcript=None):
    try:
        require_speech(data, transcript=transcript)
    except NoSpeechError:
        return False
    return True


class KnownPresenceFalseAccept(AssertionError):
    """Only the documented acceptance failure; corpus integrity errors must fail."""


def expected_negative(identity):
    marks = []
    if identity in KNOWN_FALSE_ACCEPTS:
        marks.append(
            pytest.mark.xfail(
                strict=True,
                raises=KnownPresenceFalseAccept,
                reason=f"Known presence false accept: {identity}; no safe lightweight policy found",
            )
        )
    return pytest.param(identity, id=identity, marks=marks)


@pytest.mark.parametrize("identity", [r["id"] for r in CORPUS if r["label"] == "positive"])
def test_existing_positive_audio_does_not_require_lexical_transcript(identity):
    data = audio(identity)
    # Includes quiet, 110-ms speech, low 54-70-Hz excerpts, sparse and TTS controls.
    for transcript in (None, "", "blorf zhak mm", "嗯噗咕啦"):
        assert accepted(data, transcript), (identity, transcript)


@pytest.mark.parametrize(
    "identity", [expected_negative(r["id"]) for r in CORPUS if r["label"] == "negative"]
)
def test_frozen_negative_presence_requirement(identity):
    entry = BY_ID[identity]
    if accepted(audio(identity), entry["transcript"]):
        raise KnownPresenceFalseAccept(f"{identity} was admitted as speech")


@pytest.mark.xfail(
    strict=True,
    raises=KnownPresenceFalseAccept,
    reason="Existing Han-count post-ASR veto makes periodic silence transcript-dependent",
)
def test_transcript_cannot_rescue_known_periodic_background():
    data = audio("silence_periodic")
    assert not accepted(data, "其实我不行")
    for transcript in (None, "", "妈", "blorf zhak"):
        if accepted(data, transcript):
            raise KnownPresenceFalseAccept("Periodic background was rescued by transcript context")


def test_presence_checks_leave_saved_pitch_evidence_unchanged():
    data = audio("silence_accidental")
    saved = json.loads(
        (ROOT / "services/api/var/f0-foundation/production/silence_accidental.json").read_text()
    )
    track = build_pitch_track(
        saved["result"],
        audio_sha256=BY_ID["silence_accidental"]["sha256"],
        tracker_source="praat_autocorrelation",
        tracker_version="saved-production",
        parameters={"provenance": "frozen production JSON"},
    )
    snapshot = track.model_dump_json()
    intervals = json.loads(
        (
            ROOT
            / "docs/research/pronunciation-v2/2026-10-05-utterance-evidence"
            / "negative-window-stress.json"
        ).read_text()
    )
    windows = next(r for r in intervals if r["recording"] == "silence_accidental")[
        "sufficient_intervals"
    ]
    assert len(windows) == 61
    for start, end in windows:
        region = project_pitch(track, start, end, timing_source="negative_window_stress")
        assert interpretation_eligibility(track, region).state == "sufficient"
    # A known rejected recording can also have independent pitch evidence. The
    # guard owns no track reference and cannot rewrite existing projections.
    original_saved = json.loads(
        (ROOT / "services/api/var/f0-foundation/production/silence_original.json").read_text()
    )
    original_track = build_pitch_track(
        original_saved["result"],
        audio_sha256=BY_ID["silence_original"]["sha256"],
        tracker_source="praat_autocorrelation",
        tracker_version="saved-production",
        parameters={"provenance": "frozen production JSON"},
    )
    original_snapshot = original_track.model_dump_json()
    assert not accepted(audio("silence_original"), "现在是下午两点半。")
    assert original_track.model_dump_json() == original_snapshot
    accepted(data, "not Mandarin")
    assert track.model_dump_json() == snapshot


class PresenceGateEscaped(Exception):
    """Stop an accepted negative before any downstream work or artifacts."""


@pytest.mark.parametrize(
    "identity",
    [
        "silence_original",
        "silence_periodic",
        pytest.param(
            "silence_accidental",
            marks=pytest.mark.xfail(
                strict=True,
                raises=PresenceGateEscaped,
                reason="Known blocker: accidental silence escapes the presence gate",
            ),
        ),
    ],
)
@pytest.mark.parametrize("endpoint", ["practice", "free_practice", "conversation", "stream"])
def test_persisted_negative_is_gated_before_feedback(
    identity,
    endpoint,
    client,
    auth_header,
    uploaded_utterance,
    session_factory,
    store,
    monkeypatch,
):
    import importlib

    interpreter, generator = Mock(), Mock()

    async def get_interpreter():
        return interpreter

    async def get_generator():
        return generator

    client.app.dependency_overrides[get_contextual_interpreter] = get_interpreter
    client.app.dependency_overrides[get_assistant_response_generator] = get_generator
    with session_factory() as db:
        utterance = db.get(Utterance, uuid.UUID(uploaded_utterance["id"]))
        asset = db.get(AudioAsset, utterance.canonical_audio_asset_id)
        data = audio(identity)
        store.path_for_processing(asset.storage_key).write_bytes(data)
        asset.sha256 = hashlib.sha256(data).hexdigest()
        with wave.open(io.BytesIO(data)) as reader:
            asset.duration_seconds = reader.getnframes() / reader.getframerate()
        run = PerceptionRun(
            account_id=utterance.account_id,
            utterance_id=utterance.id,
            provider="saved-fixture",
            product="test",
            adapter_version="1",
            status="succeeded",
            transcript=BY_ID[identity]["transcript"],
        )
        db.add(run)
        db.commit()
        perception_id = str(run.id)
    module_name, guard_name = {
        "practice": ("benma_api.api.routes", "require_saved_speech"),
        "free_practice": ("benma_api.pronunciation.perceived", "require_speech"),
        "conversation": ("benma_api.conversation.service", "require_speech"),
        "stream": ("benma_api.api.routes", "require_speech"),
    }[endpoint]
    module = importlib.import_module(module_name)
    original_guard = getattr(module, guard_name)

    def guard_then_stop(*args, **kwargs):
        original_guard(*args, **kwargs)
        raise PresenceGateEscaped

    # Execute the REAL guard. The sentinel prevents an accepted negative from
    # running interpretation; strict XFAIL catches only this known escape.
    monkeypatch.setattr(module, guard_name, guard_then_stop)
    if endpoint == "practice":
        for target_text in ("妈", "与原文无关"):
            target = client.post(
                "/v1/pronunciation-targets", headers=auth_header, json={"text": target_text}
            ).json()
            response = client.post(
                "/v1/pronunciation-attempts",
                headers=auth_header,
                json={"utterance_id": uploaded_utterance["id"], "target_id": target["id"]},
            )
            assert response.status_code == 422
            assert response.json()["error"]["code"] == "no_speech"
    else:
        if endpoint == "free_practice":
            path = f"/v1/perceptions/{perception_id}/speech-analysis"
            body = {}
        else:
            conversation = client.post("/v1/conversations", headers=auth_header, json={}).json()
            suffix = "/stream" if endpoint == "stream" else ""
            path = f"/v1/conversations/{conversation['id']}/user-turns{suffix}"
            body = {"utterance_id": uploaded_utterance["id"], "perception_run_id": perception_id}
        response = client.post(path, headers=auth_header, json=body)
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "no_speech"
    interpreter.interpret.assert_not_called()
    generator.generate.assert_not_called()
    with session_factory() as db:
        for model in (ConversationTurn, PronunciationAttempt, PerceivedSpeechAnalysis):
            assert db.scalar(select(func.count()).select_from(model)) == 0
        assert (
            db.get(PerceptionRun, uuid.UUID(perception_id)).transcript
            == BY_ID[identity]["transcript"]
        )

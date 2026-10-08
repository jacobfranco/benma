from __future__ import annotations

import io
import uuid
import wave
from unittest.mock import Mock

import numpy as np
import pytest
from conftest import ApiClient
from sqlalchemy import func, select

from benma_api.api.routes import get_assistant_response_generator, get_contextual_interpreter
from benma_api.audio.presence import require_speech, speech_presence
from benma_api.db.models import (
    AudioAsset,
    ConversationTurn,
    PerceptionRun,
    PronunciationAttempt,
    Utterance,
)
from benma_api.errors import NoSpeechError
from benma_api.perception.repository import SqlPerceptionRepository
from benma_api.perception.service import PerceptionService


def pcm(values: np.ndarray) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(16000)
        stream.writeframes((np.clip(values, -1, 1) * 32767).astype("<i2").tobytes())
    return output.getvalue()


def noise(level: float, click: bool = False) -> bytes:
    values = np.random.default_rng(23).normal(0, level, 32000)
    if click:
        values[12000:12004] += 0.5
    return pcm(values)


@pytest.mark.parametrize(
    "audio",
    [pcm(np.zeros(16000)), noise(0.00003), noise(0.003), noise(0.003, True)],
    ids=["silence", "near-silence", "room-noise", "click"],
)
def test_absence_rejected_without_transcript(audio: bytes) -> None:
    assert speech_presence(audio).no_speech
    with pytest.raises(NoSpeechError, match="Didn't catch any speech"):
        require_speech(audio)


@pytest.mark.parametrize(
    "duration,amplitude", [(0.055, 0.01), (0.09, 0.00015), (0.15, 0.01), (1.5, 0.1)]
)
def test_short_and_quiet_voiced_evidence_is_not_rejected(duration: float, amplitude: float) -> None:
    t = np.arange(round(duration * 16000)) / 16000
    audio = pcm(amplitude * np.sin(2 * np.pi * 170 * t))
    assert not speech_presence(audio).no_speech
    assert speech_presence(audio) == speech_presence(audio)


def test_quiet_aperiodic_activity_does_not_require_pitch() -> None:
    values = np.random.default_rng(4).normal(0, 0.0001, 16000)
    values[3000:6500] *= 8  # Whisper-like activity: explicitly not a real speech fixture.
    result = speech_presence(pcm(values))
    assert result.periodic_seconds == 0
    assert not result.no_speech


@pytest.mark.parametrize(
    "audio", [pcm(np.zeros(16000)), noise(0.003, True)], ids=["silence", "click"]
)
def test_no_speech_upload_creates_no_utterance_or_attempt(
    client, auth_header, session_factory, audio
):
    response = client.post(
        "/v1/utterances", headers=auth_header, files={"file": ("silence.wav", audio, "audio/wav")}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "no_speech", response.text
    with session_factory() as db:
        for model in (Utterance, PerceptionRun, PronunciationAttempt, ConversationTurn):
            assert db.scalar(select(func.count()).select_from(model)) == 0
        # Original evidence survives; rejected canonical data is not successful history.
        assert list(db.scalars(select(AudioAsset.kind))) == ["original"]


def legacy_silence(uploaded_utterance, session_factory, store):
    """Simulate an upload saved before the guard, without altering production rows."""
    with session_factory() as db:
        utterance = db.get(Utterance, uuid.UUID(uploaded_utterance["id"]))
        asset = db.get(AudioAsset, utterance.canonical_audio_asset_id)
        store.path_for_processing(asset.storage_key).write_bytes(pcm(np.zeros(16000)))
        return utterance.account_id, utterance.id


def test_provider_cannot_hallucinate_success_on_legacy_silence(
    uploaded_utterance,
    session_factory,
    store,
):
    account, utterance = legacy_silence(uploaded_utterance, session_factory, store)
    provider = Mock(provider_name="hallucinating", product_name="test", adapter_version="1")
    provider.request_configuration = {}
    with session_factory() as db:
        with pytest.raises(NoSpeechError):
            PerceptionService(SqlPerceptionRepository(db), store, provider).run(
                account_id=account,
                utterance_id=utterance,
                language_hint="zh",
                timeout_seconds=1,
            )
        provider.perceive.assert_not_called()
        run = db.scalar(select(PerceptionRun))
        assert run.status == "failed" and run.transcript is None and run.error_code == "no_speech"


@pytest.mark.parametrize("hum", [False, True])
def test_legacy_hallucination_cannot_create_attempt_graph_or_conversation(
    client: ApiClient,
    hum,
    auth_header,
    uploaded_utterance,
    session_factory,
    store,
):
    interpreter, generator = Mock(), Mock()

    async def get_interpreter():
        return interpreter

    async def get_generator():
        return generator

    client.app.dependency_overrides[get_contextual_interpreter] = get_interpreter
    client.app.dependency_overrides[get_assistant_response_generator] = get_generator
    account, utterance = legacy_silence(uploaded_utterance, session_factory, store)
    with session_factory() as db:
        if hum:
            asset = db.get(AudioAsset, db.get(Utterance, utterance).canonical_audio_asset_id)
            store.path_for_processing(asset.storage_key).write_bytes(periodic_background())
        run = PerceptionRun(
            account_id=account,
            utterance_id=utterance,
            provider="fixture",
            product="test",
            adapter_version="1",
            status="succeeded",
            transcript="现在是下午两点半。",
        )
        db.add(run)
        db.commit()
        perception = str(run.id)
    target = client.post(
        "/v1/pronunciation-targets", headers=auth_header, json={"text": "妈"}
    ).json()
    attempt = client.post(
        "/v1/pronunciation-attempts",
        headers=auth_header,
        json={"utterance_id": str(utterance), "target_id": target["id"]},
    )
    assert attempt.status_code == 422 and attempt.json()["error"]["code"] == "no_speech"
    graph = client.post(
        f"/v1/perceptions/{perception}/speech-analysis", headers=auth_header, json={}
    )
    assert graph.status_code == 422 and graph.json()["error"]["code"] == "no_speech"
    conversation = client.post("/v1/conversations", headers=auth_header, json={}).json()
    for suffix in ["", "/stream"]:
        reply = client.post(
            f"/v1/conversations/{conversation['id']}/user-turns{suffix}",
            headers=auth_header,
            json={"utterance_id": str(utterance), "perception_run_id": perception},
        )
        assert reply.status_code == 422 and reply.json()["error"]["code"] == "no_speech"
    interpreter.interpret.assert_not_called()
    generator.generate.assert_not_called()
    with session_factory() as db:
        assert db.scalar(select(func.count()).select_from(ConversationTurn)) == 0
        assert db.scalar(select(func.count()).select_from(PronunciationAttempt)) == 0
        assert db.get(PerceptionRun, uuid.UUID(perception)).transcript == "现在是下午两点半。"


def periodic_background() -> bytes:
    """Hum plus stationary noise: periodicity alone cannot corroborate a sentence."""
    t = np.arange(48000) / 16000
    return pcm(
        0.003 * np.sin(2 * np.pi * 60 * t) + np.random.default_rng(82).normal(0, 0.001, len(t))
    )


def test_periodic_background_cannot_corroborate_multi_character_transcript() -> None:
    from benma_api.audio.presence import corroborate_transcript

    presence = speech_presence(periodic_background())
    assert not presence.no_speech  # Deliberately permissive pre-ASR stage.
    assert presence.activity_seconds == 0 and presence.periodic_seconds > 0
    with pytest.raises(NoSpeechError):
        corroborate_transcript(presence, "其实我不行")
    # Neither lexical identity nor target agreement influences this decision.
    with pytest.raises(NoSpeechError):
        corroborate_transcript(presence, "我想买雨伞")
    corroborate_transcript(presence, "妈")


@pytest.mark.parametrize("duration,units", [(0.15, 3), (0.25, 8), (0.4, 12)])
def test_broad_corroboration_bounds_preserve_fast_quiet_voicing(duration, units) -> None:
    t = np.arange(round(duration * 16000)) / 16000
    require_speech(pcm(0.00015 * np.sin(2 * np.pi * 170 * t)), transcript="我" * units)


def test_post_asr_rejection_persists_failure_without_product_transcript(
    uploaded_utterance,
    session_factory,
    store,
):
    from benma_api.speech.contracts import PerceptionEvidence, PerceptionProviderResponse

    with session_factory() as db:
        utterance = db.get(Utterance, uuid.UUID(uploaded_utterance["id"]))
        asset = db.get(AudioAsset, utterance.canonical_audio_asset_id)
        store.path_for_processing(asset.storage_key).write_bytes(periodic_background())
        provider = Mock(provider_name="test", product_name="test", adapter_version="1")
        provider.request_configuration = {}
        provider.perceive.return_value = PerceptionProviderResponse(
            evidence=PerceptionEvidence(
                transcript="其实我不行",
                alternatives=None,
                tokens=None,
                segments=None,
                provider_uncertainty=None,
                detected_language="zh",
                evidence_status="live_provider",
            ),
            raw_payload={"text": "其实我不行"},
        )
        with pytest.raises(NoSpeechError):
            PerceptionService(SqlPerceptionRepository(db), store, provider).run(
                account_id=utterance.account_id,
                utterance_id=utterance.id,
                language_hint="zh",
                timeout_seconds=1,
            )
        run = db.scalar(select(PerceptionRun))
        assert run.status == "failed" and run.transcript is None
        assert run.error_code == "no_speech"
        assert run.raw_payload_json == {"text": "其实我不行"}  # Audit evidence only.
        assert run.normalized_result["speech_presence"]["corroboration_checked"]
        assert db.scalar(select(func.count()).select_from(PronunciationAttempt)) == 0
        assert db.scalar(select(func.count()).select_from(ConversationTurn)) == 0


@pytest.mark.parametrize("case", [6, 10])
def test_exact_local_false_accept_replay(case) -> None:
    """Opt-in private fixtures; persisted IDs/hashes, never checked-in user audio."""
    import hashlib
    import json
    import os
    from pathlib import Path

    location = os.environ.get("BENMA_TRUST_RECORDINGS")
    if not location:
        pytest.skip("set BENMA_TRUST_RECORDINGS to the local evidence inventory")
    rows = json.loads(Path(location).read_text())
    expected = {
        6: ("de4b999e-a527-4613-8709-618c68716477", "现在是下午两点半。"),
        10: ("ab6c16ab-ece9-4d00-a3f9-ca693d103624", "其实我不行"),
    }
    identity, text = expected[case]
    record = next(r for r in rows if r["perception_id"] == identity)
    data = Path(record["path"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == record["sha256"]
    assert record["transcript"] == text
    with pytest.raises(NoSpeechError):
        require_speech(data, transcript=text)


def test_cached_target_assessment_cannot_bypass_later_no_speech_failure(
    client,
    auth_header,
    uploaded_utterance,
    session_factory,
):
    from benma_api.db.models import AssessmentRun, PronunciationInterpretationRun

    target = client.post(
        "/v1/pronunciation-targets", headers=auth_header, json={"text": "妈"}
    ).json()
    attempt = client.post(
        "/v1/pronunciation-attempts",
        headers=auth_header,
        json={"utterance_id": uploaded_utterance["id"], "target_id": target["id"]},
    ).json()
    path = f"/v1/pronunciation-attempts/{attempt['id']}/analyze"
    assert client.post(path, headers=auth_header, json={}).status_code == 200
    with session_factory() as db:
        utterance = db.get(Utterance, uuid.UUID(uploaded_utterance["id"]))
        db.add(
            PerceptionRun(
                account_id=utterance.account_id,
                utterance_id=utterance.id,
                provider="fixture",
                product="fixture",
                adapter_version="1",
                status="failed",
                error_code="no_speech",
            )
        )
        db.commit()
        before = [
            db.scalar(select(func.count()).select_from(m))
            for m in [AssessmentRun, PronunciationInterpretationRun]
        ]
    response = client.post(path, headers=auth_header, json={"reuse_existing": True})
    assert response.status_code == 422 and response.json()["error"]["code"] == "no_speech"
    with session_factory() as db:
        assert [
            db.scalar(select(func.count()).select_from(m))
            for m in [AssessmentRun, PronunciationInterpretationRun]
        ] == before

from __future__ import annotations

import copy
import threading
import uuid
from unittest.mock import Mock

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.dialects import postgresql

from benma_api.db.models import (
    AcousticRun,
    ContextualInterpretationRun,
    PerceivedSpeechAnalysis,
    PerceptionRun,
    PronunciationAttempt,
    PronunciationTarget,
    Utterance,
)
from benma_api.pronunciation.acoustics import AutocorrelationAcousticAnalyzer, _downsample
from benma_api.pronunciation.alignment import AlignmentResponse, DisabledAligner
from benma_api.pronunciation.perceived import (
    PerceivedSpeechAnalysisService,
    analysis_response,
    perceived_syllables,
)


def perception_for(session_factory, utterance, text="周谋", status="succeeded", **evidence):
    with session_factory() as db:
        source = db.get(Utterance, uuid.UUID(str(utterance["id"])))
        run = PerceptionRun(
            account_id=source.account_id,
            utterance_id=source.id,
            provider="fixture",
            product="test",
            adapter_version="1",
            status=status,
            transcript=text,
            normalized_result={"transcript": text, **evidence},
            raw_payload_json={"immutable": True},
        )
        db.add(run)
        db.commit()
        return run


def analyze(client, auth_header, perception):
    response = client.post(
        f"/v1/perceptions/{perception.id}/speech-analysis", headers=auth_header, json={}
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize(
    "decision,text",
    [
        ("preserve", "你好，今天我们聊周谋。"),
        ("infer", "周谋"),
        ("clarify", "你好，今天我……"),
    ],
)
def test_perception_is_the_reference_regardless_of_semantics(
    client,
    auth_header,
    uploaded_utterance,
    session_factory,
    decision,
    text,
):
    perception = perception_for(session_factory, uploaded_utterance, text)
    with session_factory() as db:
        db.add(
            ContextualInterpretationRun(
                account_id=perception.account_id,
                perception_run_id=perception.id,
                interpreter="fixture",
                interpreter_version="1",
                context_snapshot={},
                decision=decision,
                inferred_text="周末" if decision == "infer" else None,
                uncertainty={},
                clarification_needed=decision == "clarify",
            )
        )
        db.commit()
    result = analyze(client, auth_header, perception)
    assert result["alignment_reference_text"] == text
    assert result["reference_kind"] == "perceived_text"
    assert result["data"]["syllables"]
    # Even silence retains an explicit measured (unvoiced) contour, never fabricated F0.
    assert result["data"]["measured_pitch"]
    assert all(point["f0_hz"] is None for point in result["data"]["measured_pitch"])
    assert result["data"]["pitch_status"] == "unavailable"
    assert "score" not in str(result)
    if decision == "infer":
        assert [s["pinyin"] for s in result["data"]["syllables"]] == ["zhōu", "móu"]
        assert [s["lexical_tone"] for s in result["data"]["syllables"]] == [1, 2]
    with session_factory() as db:
        assert db.scalar(select(func.count()).select_from(PronunciationTarget)) == 0
        assert db.scalar(select(func.count()).select_from(PronunciationAttempt)) == 0
        stored = db.get(PerceivedSpeechAnalysis, uuid.UUID(result["id"]))
        assert stored.perception_run_id == perception.id
        assert stored.audio_sha256
        assert stored.configuration["reading_engine"].startswith("pypinyin-")
        assert db.get(AcousticRun, stored.acoustic_run_id).utterance_id == perception.utterance_id
        assert db.get(PerceptionRun, perception.id).transcript == text


def test_punctuation_offsets_neutral_and_ambiguous_readings():
    syllables = perceived_syllables("你好，我们！行……123 OK", {})
    assert [s.characters for s in syllables] == list("你好我们行")
    assert [s.character_start for s in syllables] == [0, 1, 3, 4, 6]
    assert [s.lexical_tone for s in syllables] == [3, 3, 3, 0, None]
    assert syllables[-2].expected_tone == []  # Neutral is not a fabricated level tone.
    assert syllables[-1].pinyin is None
    assert set(syllables[-1].alternatives) >= {"xing2", "hang2"}
    assert perceived_syllables("，……[123]", {}) == []
    assert perceived_syllables("银行", {})[-1].pinyin == "háng"
    assert [point.height for point in perceived_syllables("谋", {})[0].expected_tone] == [0.5, 1.0]


def test_only_exact_persisted_pronunciation_token_can_resolve_polyphone():
    token = {"character_start": 0, "character_end": 1, "text": "行", "pinyin": "hang2"}
    syllable = perceived_syllables("行", {"tokens": [token]})[0]
    assert (syllable.pinyin, syllable.lexical_tone, syllable.reading_source) == (
        "háng",
        2,
        "perception_token",
    )
    for change in [{"text": "末"}, {"character_end": 2}, {"pinyin": "invalid"}]:
        assert perceived_syllables("行", {"tokens": [{**token, **change}]})[0].pinyin is None
    assert (
        perceived_syllables("行", {"tokens": [{"token": "行", "logprob": -0.1}]})[0].pinyin is None
    )


def test_correction_appends_without_rewriting_analysis_and_requests_reuse(
    client,
    auth_header,
    uploaded_utterance,
    session_factory,
):
    perception = perception_for(session_factory, uploaded_utterance)
    original = analyze(client, auth_header, perception)
    response = client.post(
        f"/v1/utterances/{perception.utterance_id}/corrections",
        headers=auth_header,
        json={"perception_run_id": str(perception.id), "intended_text": "周末"},
    )
    assert response.status_code == 201, response.text
    assert analyze(client, auth_header, perception) == original
    assert (
        client.get(f"/v1/perceived-speech-analyses/{original['id']}", headers=auth_header).json()
        == original
    )
    with session_factory() as db:
        assert db.scalar(select(func.count()).select_from(PerceivedSpeechAnalysis)) == 1
        assert db.scalar(select(func.count()).select_from(AcousticRun)) == 1
        for cls, identity, attribute in [
            (PerceivedSpeechAnalysis, uuid.UUID(original["id"]), "alignment_reference_text"),
            (PerceptionRun, perception.id, "transcript"),
        ]:
            record = db.get(cls, identity)
            setattr(record, attribute, "周末")
            with pytest.raises(ValueError, match="append-only"):
                db.flush()
            db.rollback()


@pytest.mark.parametrize(
    "field", ["alignment_reference_text", "inferred_text", "target_id", "text"]
)
def test_client_cannot_supply_reference(
    client, auth_header, uploaded_utterance, session_factory, field
):
    perception = perception_for(session_factory, uploaded_utterance)
    response = client.post(
        f"/v1/perceptions/{perception.id}/speech-analysis",
        headers=auth_header,
        json={field: "周末"},
    )
    assert response.status_code == 422


def test_analysis_ownership(client, auth_header, uploaded_utterance, session_factory):
    perception = perception_for(session_factory, uploaded_utterance)
    result = analyze(client, auth_header, perception)
    token = client.post("/v1/dev/auth", json={"phone_number": "+12025550124"}).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert (
        client.post(
            f"/v1/perceptions/{perception.id}/speech-analysis", headers=headers, json={}
        ).status_code
        == 404
    )
    assert (
        client.get(f"/v1/perceived-speech-analyses/{result['id']}", headers=headers).status_code
        == 404
    )


@pytest.mark.parametrize("text,status", [("", "succeeded"), ("ignored", "failed")])
def test_requires_successful_nonempty_perception(
    client,
    auth_header,
    uploaded_utterance,
    session_factory,
    text,
    status,
):
    perception = perception_for(session_factory, uploaded_utterance, text, status)
    assert (
        client.post(
            f"/v1/perceptions/{perception.id}/speech-analysis", headers=auth_header, json={}
        ).status_code
        == 422
    )


def test_disabled_alignment_does_not_hide_actual_pitch(
    client,
    auth_header,
    session_factory,
    settings,
    store,
    tmp_path,
):
    from test_pronunciation_laboratory import _chirp

    path = tmp_path / "rising.wav"
    _chirp(path, start_hz=150, end_hz=250, seconds=0.4)
    utterance = client.post(
        "/v1/utterances",
        headers=auth_header,
        files={"file": ("rising.wav", path.read_bytes(), "audio/wav")},
    ).json()
    perception = perception_for(session_factory, utterance, "你好，今天我……")
    with session_factory() as db:
        run = PerceivedSpeechAnalysisService(db, store, settings, aligner=DisabledAligner()).run(
            account_id=perception.account_id, perception_run_id=perception.id
        )
        response = analysis_response(run)
    assert response.status == "partial"
    assert response.data.pitch_status == "available"
    assert response.data.alignment_status == "unavailable"
    assert all(s.start_seconds is None for s in response.data.syllables)
    assert len([p for p in response.data.measured_pitch if p.f0_hz]) > 10
    assert all(p.f0_hz is None or 50 <= p.f0_hz <= 550 for p in response.data.measured_pitch)
    assert response.data.syllables[0].expected_tone
    serialized = response.model_dump_json()
    for private in ["raw_payload", "storage_key", "configuration", str(path), "api_key"]:
        assert private not in serialized


def test_pitch_and_alignment_overlap_without_worker_sql(
    uploaded_utterance,
    session_factory,
    settings,
    store,
):
    perception = perception_for(session_factory, uploaded_utterance, "周谋")
    barrier = threading.Barrier(2, timeout=5)
    analyzer = Mock(algorithm_name="test-pitch", algorithm_version="1", parameters={})
    aligner = Mock(algorithm_name="test-alignment", algorithm_version="1")
    owner = threading.get_ident()
    sql_threads = []

    def pitch(path):
        barrier.wait()
        return AutocorrelationAcousticAnalyzer().analyze(path)

    def align(request):
        barrier.wait()
        assert request.reference_text == "周谋"
        return AlignmentResponse(
            units=[
                {"label": "zhōu", "start_seconds": 0.0, "end_seconds": 0.075},
                {"label": "móu", "start_seconds": 0.075, "end_seconds": 0.15},
            ],
            raw_result={"private": "must not leak"},
            evidence_status="live_tool",
        )

    analyzer.analyze.side_effect = pitch
    aligner.align.side_effect = align
    with session_factory() as db:

        def sql(*args):
            sql_threads.append(threading.get_ident())

        event.listen(db.bind, "before_cursor_execute", sql)
        try:
            run = PerceivedSpeechAnalysisService(
                db, store, settings, analyzer=analyzer, aligner=aligner
            ).run(account_id=perception.account_id, perception_run_id=perception.id)
        finally:
            event.remove(db.bind, "before_cursor_execute", sql)
    assert set(sql_threads) == {owner}
    assert run.result["alignment_status"] == "aligned"
    assert [s["start_seconds"] for s in run.result["syllables"]] == [0.0, 0.075]
    assert run.result["alignment_latency_ms"] >= 0
    assert "private" not in str(run.result)


def test_pitch_failure_is_persisted_without_losing_reference_or_meaning(
    uploaded_utterance,
    session_factory,
    settings,
    store,
):
    perception = perception_for(session_factory, uploaded_utterance)
    analyzer = Mock(algorithm_name="broken", algorithm_version="1", parameters={})
    analyzer.analyze.side_effect = RuntimeError("SECRET must not leak")
    with session_factory() as db:
        service = PerceivedSpeechAnalysisService(db, store, settings, analyzer=analyzer)
        run = service.run(account_id=perception.account_id, perception_run_id=perception.id)
        assert run.status == "failed"
        assert run.result["measured_pitch"] == []
        assert run.alignment_reference_text == "周谋"
        assert run.result["syllables"]
        assert "SECRET" not in analysis_response(run).model_dump_json()
        # Failed evidence is also idempotent; config/version changes append a separate run.
        assert (
            service.run(account_id=perception.account_id, perception_run_id=perception.id).id
            == run.id
        )
        assert analyzer.analyze.call_count == 1
        analyzer.algorithm_version = "2"
        assert (
            service.run(account_id=perception.account_id, perception_run_id=perception.id).id
            != run.id
        )


def test_downsampling_keeps_tail_and_gaps():
    points = [
        {
            "timestamp_seconds": i / 100,
            "normalized_semitones": None if 250 <= i <= 350 else float(i % 7),
        }
        for i in range(1000)
    ]
    result = _downsample(copy.deepcopy(points))
    assert len(result) <= 240
    assert result[0] == points[0]
    assert result[-1] == points[-1]
    assert any(p["normalized_semitones"] is None for p in result)


def test_analysis_lock_does_not_block_interpretation_foreign_key():
    sql = str(
        select(PerceptionRun).with_for_update(key_share=True).compile(dialect=postgresql.dialect())
    )
    assert "FOR NO KEY UPDATE" in sql


@pytest.mark.parametrize(
    "units",
    [
        [
            {"label": "wrong", "start_seconds": 0, "end_seconds": 0.075},
            {"label": "tier", "start_seconds": 0.075, "end_seconds": 0.15},
        ],
        [
            {"label": "zhou1", "start_seconds": float("nan"), "end_seconds": 0.075},
            {"label": "mou2", "start_seconds": 0.075, "end_seconds": 0.15},
        ],
    ],
)
def test_invalid_alignment_never_becomes_syllable_timing(
    uploaded_utterance,
    session_factory,
    settings,
    store,
    units,
):
    perception = perception_for(session_factory, uploaded_utterance)
    aligner = Mock(algorithm_name="bad-alignment", algorithm_version="1")
    aligner.align.return_value = AlignmentResponse(
        units=units, raw_result=None, evidence_status="live_tool"
    )
    with session_factory() as db:
        run = PerceivedSpeechAnalysisService(db, store, settings, aligner=aligner).run(
            account_id=perception.account_id, perception_run_id=perception.id
        )
    assert run.result["alignment_status"] == "unavailable"
    assert all(s["start_seconds"] is None for s in run.result["syllables"])
    assert run.result["measured_pitch"]


@pytest.mark.parametrize("synthetic", [False, True])
def test_exact_token_timing_enables_shape_without_forced_aligner(
    uploaded_utterance,
    session_factory,
    settings,
    store,
    synthetic,
):
    from test_readings_contours import raw_contour

    token = {
        "text": "末",
        "character_start": 0,
        "character_end": 1,
        "timing": {"start_seconds": 0, "end_seconds": 0.15},
    }
    perception = perception_for(
        session_factory,
        uploaded_utterance,
        "末",
        tokens=[token],
        evidence_status="synthetic_replay" if synthetic else "live_provider",
    )
    raw = raw_contour([0] * 15)
    analyzer = Mock(algorithm_name="fixture", algorithm_version="1", parameters={})
    analyzer.analyze.return_value = {"f0": raw, "mobile_f0": raw}
    with session_factory() as db:
        run = PerceivedSpeechAnalysisService(
            db, store, settings, analyzer=analyzer, aligner=DisabledAligner()
        ).run(account_id=perception.account_id, perception_run_id=perception.id)
        syllable = run.result["syllables"][0]
        assert run.result["alignment_status"] == ("synthetic" if synthetic else "aligned")
        assert syllable["lexical_tone"] == 4
        assert syllable["pinyin"] == "mò"
        assert syllable["observed_contour"]["classification"] == (
            "unclear" if synthetic else "1-like"
        )
        if synthetic:
            assert syllable["display_contour"] is None
        else:
            assert syllable["display_contour"]["segments"]
        assert db.get(AcousticRun, run.acoustic_run_id).normalized_result["f0"] == raw


@pytest.mark.parametrize(
    "token",
    [
        {
            "text": "周末",
            "character_start": 0,
            "character_end": 2,
            "timing": {"start_seconds": 0, "end_seconds": 0.15},
        },
        {
            "text": "末",
            "character_start": 0,
            "character_end": 1,
            "timing": {"start_seconds": 0, "end_seconds": 9},
        },
    ],
)
def test_word_or_invalid_token_timing_never_fabricates_syllables(
    uploaded_utterance,
    session_factory,
    settings,
    store,
    token,
):
    perception = perception_for(session_factory, uploaded_utterance, "周末", tokens=[token])
    with session_factory() as db:
        run = PerceivedSpeechAnalysisService(db, store, settings, aligner=DisabledAligner()).run(
            account_id=perception.account_id, perception_run_id=perception.id
        )
    assert run.result["alignment_status"] == "unavailable"
    assert all(s["display_contour"] is None for s in run.result["syllables"])


def test_two_real_token_intervals_slice_only_their_own_learner_contour(
    client,
    auth_header,
    session_factory,
    settings,
    store,
    tmp_path,
):
    from test_pronunciation_laboratory import _chirp
    from test_readings_contours import raw_contour

    path = tmp_path / "two-syllables.wav"
    _chirp(path, start_hz=160, end_hz=220, seconds=0.6)
    utterance = client.post(
        "/v1/utterances",
        headers=auth_header,
        files={"file": ("two.wav", path.read_bytes(), "audio/wav")},
    ).json()
    tokens = [
        {
            "text": character,
            "character_start": i,
            "character_end": i + 1,
            "timing": {"start_seconds": i * 0.3, "end_seconds": (i + 1) * 0.3},
        }
        for i, character in enumerate("周末")
    ]
    perception = perception_for(session_factory, utterance, "周末", tokens=tokens)
    raw = raw_contour([i * 0.15 for i in range(30)] + [4.35 - i * 0.15 for i in range(30)])
    analyzer = Mock(algorithm_name="fixture", algorithm_version="1", parameters={})
    analyzer.analyze.return_value = {"f0": raw, "mobile_f0": raw}
    with session_factory() as db:
        run = PerceivedSpeechAnalysisService(
            db, store, settings, analyzer=analyzer, aligner=DisabledAligner()
        ).run(account_id=perception.account_id, perception_run_id=perception.id)
    first, second = run.result["syllables"]
    assert [first["lexical_tone"], second["lexical_tone"]] == [1, 4]
    assert [
        first["observed_contour"]["classification"],
        second["observed_contour"]["classification"],
    ] == ["2-like", "4-like"]
    for syllable in (first, second):
        assert all(
            syllable["start_seconds"] <= p["timestamp_seconds"] < syllable["end_seconds"]
            for segment in syllable["display_contour"]["segments"]
            for p in segment
        )


def test_multi_character_word_tier_is_not_split_to_fake_syllables(
    uploaded_utterance,
    session_factory,
    settings,
    store,
):
    from benma_api.pronunciation.alignment import parse_textgrid

    textgrid = (
        'item [1]:\nname = "words"\nintervals [1]:\nxmin = 0\nxmax = 0.15\ntext = "周末"\n'
        'item [2]:\nname = "phones"\nintervals [1]:\nxmin = 0\nxmax = 0.04\ntext = "zh"'
    )
    perception = perception_for(session_factory, uploaded_utterance, "周末")
    aligner = Mock(algorithm_name="fixture", algorithm_version="1")
    aligner.align.return_value = AlignmentResponse(
        units=parse_textgrid(textgrid), raw_result=None, evidence_status="live_tool"
    )
    with session_factory() as db:
        run = PerceivedSpeechAnalysisService(db, store, settings, aligner=aligner).run(
            account_id=perception.account_id, perception_run_id=perception.id
        )
    assert run.result["alignment_status"] == "unavailable"
    assert [s["pinyin"] for s in run.result["syllables"]] == ["zhōu", "mò"]
    assert all(
        s["start_seconds"] is None and s["observed_contour"]["classification"] == "unclear"
        for s in run.result["syllables"]
    )

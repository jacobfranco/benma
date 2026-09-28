"""Opt-in real PostgreSQL concurrency check in an isolated temporary schema.

BENMA_TEST_POSTGRES=1 uses the configured development DB, creates a uniquely named
schema, and drops only that schema afterward. It never calls a live speech provider.
"""

from __future__ import annotations

import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker

from benma_api.config import Settings
from benma_api.db.base import Base
from benma_api.db.models import (
    Account,
    AcousticRun,
    AudioAsset,
    ContextualInterpretationRun,
    PerceivedSpeechAnalysis,
    PerceptionRun,
    Utterance,
)
from benma_api.perception.repository import SqlPerceptionRepository
from benma_api.perception.service import PerceptionService
from benma_api.pronunciation.acoustics import AcousticAnalysisService
from benma_api.pronunciation.alignment import DisabledAligner
from benma_api.pronunciation.perceived import PerceivedSpeechAnalysisService
from benma_api.pronunciation.warmup import start_acoustic_warmup
from benma_api.speech.providers.replay import ReplayPerceptionProvider


@pytest.mark.skipif(os.getenv("BENMA_TEST_POSTGRES") != "1", reason="opt-in local PostgreSQL check")
@pytest.mark.parametrize("warmup", [False, True])
def test_duplicate_analysis_and_context_insertion_are_independent(store, monkeypatch, warmup):
    settings = Settings()
    engine = create_engine(settings.database_url)
    schema = "benma_analysis_test_" + uuid.uuid4().hex
    translated = engine.execution_options(schema_translate_map={None: schema})
    session_factory = sessionmaker(translated, expire_on_commit=False)
    release = threading.Event()
    entered = threading.Event()
    analyzer = Mock(algorithm_name="test-pitch", algorithm_version="1", parameters={})

    def compute(_path):
        entered.set()
        assert release.wait(timeout=5), "meaning/FK insert was blocked by optional analysis"
        return {"mobile_f0": [], "contour_features": {"voiced_fraction": 0}}

    analyzer.analyze.side_effect = compute
    monkeypatch.setattr(
        "benma_api.pronunciation.warmup.build_acoustic_analyzer", lambda _: analyzer
    )
    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    try:
        Base.metadata.create_all(translated)
        with session_factory() as db:
            account = Account()
            db.add(account)
            db.flush()
            asset = AudioAsset(
                account_id=account.id,
                storage_key="test/recording.wav",
                kind="canonical",
                mime_type="audio/wav",
                sha256="0" * 64,
                size_bytes=0,
                duration_seconds=1,
            )
            db.add(asset)
            db.flush()
            utterance = Utterance(
                account_id=account.id,
                original_audio_asset_id=asset.id,
                canonical_audio_asset_id=asset.id,
            )
            db.add(utterance)
            db.flush()
            perception = PerceptionRun(
                account_id=account.id,
                utterance_id=utterance.id,
                transcript="周谋",
                provider="fixture",
                product="test",
                adapter_version="1",
                status="succeeded",
                normalized_result={"transcript": "周谋"},
            )
            db.add(perception)
            db.commit()
            account_id, perception_id, utterance_id = account.id, perception.id, utterance.id

        def analyze():
            with session_factory() as db:
                return (
                    PerceivedSpeechAnalysisService(
                        db, store, settings, analyzer=analyzer, aligner=DisabledAligner()
                    )
                    .run(account_id=account_id, perception_run_id=perception_id)
                    .id
                )

        def interpret():
            with session_factory() as db:
                db.execute(text("SET LOCAL lock_timeout = '2s'"))
                # Simulated ASR can finish and persist while acoustics are held.
                assert entered.is_set() and not release.is_set()
                audio_store = Mock()
                audio_store.read.return_value = b"fixture audio"
                asr = PerceptionService(
                    SqlPerceptionRepository(db), audio_store, ReplayPerceptionProvider()
                ).run(
                    account_id=account_id,
                    utterance_id=utterance_id,
                    language_hint="zh",
                    timeout_seconds=3,
                )
                assert asr.status == "succeeded" and not release.is_set()
                db.add(
                    ContextualInterpretationRun(
                        account_id=account_id,
                        perception_run_id=perception_id,
                        interpreter="fixture",
                        interpreter_version="1",
                        context_snapshot={},
                        decision="preserve",
                        uncertainty={},
                        clarification_needed=False,
                    )
                )
                db.commit()

        warm = None
        if warmup:
            with session_factory() as db:
                warm = start_acoustic_warmup(
                    db, store, settings, account_id=account_id, utterance_id=utterance_id
                )
                assert warm is not None
                assert entered.wait(timeout=3)
                assert (
                    start_acoustic_warmup(
                        db, store, settings, account_id=account_id, utterance_id=utterance_id
                    )
                    is warm
                )

        def acoustic_endpoint():
            with session_factory() as db:
                return (
                    AcousticAnalysisService(db, store, analyzer)
                    .run(account_id=account_id, utterance_id=utterance_id)
                    .id
                )

        with ThreadPoolExecutor(max_workers=4) as pool:
            first = pool.submit(analyze)
            assert entered.wait(timeout=3)
            second = pool.submit(analyze)
            acoustic = pool.submit(acoustic_endpoint)
            try:
                pool.submit(interpret).result(timeout=3)
                assert not first.done()
            finally:
                release.set()
            assert first.result(timeout=5) == second.result(timeout=5)
            acoustic_id = acoustic.result(timeout=5)
            if warm is not None:
                assert warm.result(timeout=5) == acoustic_id
        assert analyzer.analyze.call_count == 1
        with session_factory() as db:
            assert db.scalar(select(func.count()).select_from(PerceivedSpeechAnalysis)) == 1
            assert db.scalar(select(func.count()).select_from(AcousticRun)) == 1
            assert db.scalar(select(func.count()).select_from(ContextualInterpretationRun)) == 1
    finally:
        release.set()
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        engine.dispose()


@pytest.mark.skipif(os.getenv("BENMA_TEST_POSTGRES") != "1", reason="opt-in local PostgreSQL check")
@pytest.mark.parametrize("warmup", [False, True])
def test_known_target_padding_reconciliation_is_single_flight(store, monkeypatch, warmup, settings):
    import json
    from pathlib import Path

    from conftest import wav_bytes

    from benma_api.db.models import AlignmentRun, PronunciationAttempt, PronunciationTarget
    from benma_api.pronunciation.alignment import AlignmentResponse
    from benma_api.pronunciation.laboratory import PronunciationLaboratoryService
    from benma_api.pronunciation.targets import parse_mandarin_target

    row = json.loads((Path(__file__).parent / "fixtures/phone_upstream_evidence.json").read_text())[
        1
    ]
    engine = create_engine(Settings().database_url)
    schema = "benma_target_test_" + uuid.uuid4().hex
    translated = engine.execution_options(schema_translate_map={None: schema})
    factory = sessionmaker(translated, expire_on_commit=False)
    release, entered = threading.Event(), threading.Event()
    analyzer = Mock(algorithm_name="test-pitch", algorithm_version="1", parameters={})
    aligner = Mock(algorithm_name="test-alignment", algorithm_version="1")
    aligner.align.return_value = AlignmentResponse(row["alignment"]["units"], {}, "live_provider")

    def compute(_):
        entered.set()
        assert release.wait(5)
        return {
            **row["acoustic"],
            "mobile_f0": row["acoustic"]["f0"],
            "recording_quality": {"status": "usable", "issues": []},
        }

    analyzer.analyze.side_effect = compute
    monkeypatch.setattr(
        "benma_api.pronunciation.laboratory.build_acoustic_analyzer", lambda _: analyzer
    )
    monkeypatch.setattr(
        "benma_api.pronunciation.warmup.build_acoustic_analyzer", lambda _: analyzer
    )
    monkeypatch.setattr("benma_api.pronunciation.laboratory.build_aligner", lambda _: aligner)
    store.put("test/padding.wav", wav_bytes(2.2059))
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    try:
        Base.metadata.create_all(translated)
        with factory() as db:
            account = Account()
            db.add(account)
            db.flush()
            asset = AudioAsset(
                account_id=account.id,
                storage_key="test/padding.wav",
                kind="canonical",
                mime_type="audio/wav",
                sha256="0" * 64,
                size_bytes=0,
                duration_seconds=2.2059,
                sample_rate_hz=16000,
            )
            db.add(asset)
            db.flush()
            utterance = Utterance(
                account_id=account.id,
                original_audio_asset_id=asset.id,
                canonical_audio_asset_id=asset.id,
            )
            parsed = parse_mandarin_target("嘛")
            target = PronunciationTarget(
                account_id=account.id,
                text="嘛",
                target_source="manual",
                pinyin_source=parsed.provenance,
                display_pinyin=parsed.display_pinyin,
                pinyin_syllables=parsed.pinyin_syllables,
                lexical_tones=parsed.lexical_tones,
                pinyin_alternatives=parsed.alternatives,
                syllable_units=parsed.syllable_units,
                surface_tone_expectation=parsed.surface_tone_expectation,
            )
            db.add_all([utterance, target])
            db.flush()
            attempt = PronunciationAttempt(
                account_id=account.id, utterance_id=utterance.id, target_id=target.id
            )
            db.add(attempt)
            db.commit()
            aid, uid, pid = account.id, utterance.id, attempt.id

        def analyze():
            with factory() as db:
                return PronunciationLaboratoryService(db, store, settings).analyze(
                    account_id=aid,
                    attempt_id=pid,
                    reuse_existing=True,
                    rerun_provider=False,
                    rerun_acoustics=False,
                    rerun_alignment=False,
                )

        warm = None
        if warmup:
            with factory() as db:
                warm = start_acoustic_warmup(db, store, settings, account_id=aid, utterance_id=uid)
            assert warm is not None and entered.wait(3)
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(analyze)
            assert entered.wait(3)
            second = pool.submit(analyze)
            release.set()
            a, b = first.result(10), second.result(10)
        assert a.acoustic.id == b.acoustic.id
        assert a.alignment.id == b.alignment.id
        assert a.interpretation.id == b.interpretation.id
        if warm:
            assert warm.result(5) == a.acoustic.id
        assert a.overall_evidence["timing_resolution"]["accepted"]
        assert a.syllables[0].observed_contour.features["raw_voiced_frames"] > 0
        assert analyzer.analyze.call_count == aligner.align.call_count == 1
        with factory() as db:
            assert db.scalar(select(func.count()).select_from(AcousticRun)) == 1
            assert db.scalar(select(func.count()).select_from(AlignmentRun)) == 1
    finally:
        release.set()
        with engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        engine.dispose()

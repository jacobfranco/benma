from __future__ import annotations

import copy
import hashlib
import json
import uuid
from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select

from benma_api.db.models import AcousticRun, AudioAsset, Utterance
from benma_api.pronunciation.acoustics import AcousticAnalysisService, PraatAcousticAnalyzer
from benma_api.pronunciation.contours import classify_contour
from benma_api.pronunciation.perceived import perceived_syllables
from benma_api.pronunciation.pitch_evidence import (
    build_pitch_track,
    display_from_track,
    gate_observation,
    interpretation_eligibility,
    load_pitch_track,
    project_pitch,
)
from benma_api.pronunciation.pitch_types import UtterancePitchTrack


def track(raw, duration=1.0):
    return build_pitch_track(
        dict(f0=raw, duration_seconds=duration),
        audio_sha256="a" * 64,
        tracker_source="saved-praat",
        tracker_version="1",
        parameters={"hop": 0.01},
    )


def coherent(hz=150, slope=0):
    return [
        dict(
            timestamp_seconds=i / 100,
            tracker_f0_hz=hz * 2 ** (slope * i / 50 / 12),
            f0_hz=hz * 2 ** (slope * i / 50 / 12),
            voicing_probability=0.95,
            quality_usable=True,
        )
        for i in range(50)
    ]


def eligibility(t, start=0, end=0.5):
    return interpretation_eligibility(
        t, project_pitch(t, start, end, timing_source="saved_grapheme")
    )


@pytest.mark.parametrize("hz,slope", [(150, 6), (180, -6), (54, 0), (60, 0), (70, 0)])
def test_complete_gestures_and_low_frequency_have_sufficient_acoustic_support(hz, slope):
    raw = coherent(hz, slope)
    t = track(raw)
    e = eligibility(t)
    assert e.state == "sufficient"
    observed = classify_contour(display_from_track(t), 0, 0.5, raw=raw, pitch_track=t)
    assert observed.classification == ({6: "2-like", -6: "4-like"}.get(slope, "1-like"))
    assert gate_observation(observed, e).classification == observed.classification


def test_truncated_tail_preserves_raw_history_and_marks_incomplete():
    raw = coherent(slope=6)
    for p in raw[30:]:
        p.update(f0_hz=None, energy_gated=True)
    before = copy.deepcopy(raw)
    t = track(raw)
    e = eligibility(t)
    assert e.state == "incomplete"
    assert e.metrics.missing_tail_seconds == pytest.approx(0.2)
    assert all(
        f.raw_f0_hz and f.selected_f0_hz is None and "below_energy_gate" in f.exclusion_reasons
        for f in t.frames[30:]
    )
    assert raw == before
    with pytest.raises(ValidationError):
        t.frames[0].raw_f0_hz = 1
    with pytest.raises(ValidationError):
        t.frames = ()
    assert UtterancePitchTrack.model_validate_json(t.model_dump_json()) == t


def test_unvoiced_initials_do_not_count_as_lost_voiced_support():
    raw = coherent()
    for p in raw[:15]:
        p.update(f0_hz=None, tracker_f0_hz=None)
    e = eligibility(track(raw))
    assert e.state == "sufficient"
    assert e.metrics.retained_fraction == 1 and e.metrics.missing_head_seconds == 0


@pytest.mark.parametrize("kind", ["gap", "jump", "sparse", "silent"])
def test_path_failures_abstain(kind):
    raw = coherent()
    if kind == "gap":
        for p in raw[15:30]:
            p.update(f0_hz=None, tracker_f0_hz=None)
    if kind == "jump":
        for p in raw[25:]:
            p.update(f0_hz=500, tracker_f0_hz=500)
    if kind in {"sparse", "silent"}:
        for p in raw[3 if kind == "sparse" else 0 :]:
            p.update(f0_hz=None, tracker_f0_hz=None)
    e = eligibility(track(raw))
    assert e.state in {"unstable", "insufficient"}
    assert e.state != "sufficient"


def test_projection_is_exact_immutable_and_lexically_independent():
    t = track(coherent())
    frozen = t.model_dump_json()
    for text in ["贵州", "鬼粥", "完全不同", "", "雨伞。"]:
        for s in perceived_syllables(text, {}):
            s.lexical_tone, s.expected_surface_tone = 4, 2
        for _ in range(2):
            p = project_pitch(
                t, 0.1, 0.2, timing_source="saved_grapheme", timing_evidence_id="same"
            )
            assert p.frame_indices == tuple(range(10, 20))
            assert [t.frames[i].timestamp_seconds for i in p.frame_indices] == [
                i / 100 for i in range(10, 20)
            ]
        assert t.model_dump_json() == frozen
    # Whole grouped word only. Internal character projection remains unavailable.
    group = project_pitch(t, 0.1, 0.5, timing_source="azure_word")
    assert group.frame_indices == tuple(range(10, 50))
    assert not project_pitch(t, None, None, timing_source=None).frame_indices
    assert not project_pitch(t, 0, 0.2, timing_source="synthetic").frame_indices
    assert not project_pitch(t, 0.5, 0.6, timing_source="saved_grapheme").frame_indices
    other = track(coherent(180))
    with pytest.raises(ValueError):
        interpretation_eligibility(other, group)


def test_legacy_replay_never_reextracts_or_overwrites_selection():
    raw = coherent()
    result = dict(f0=raw, duration_seconds=1)
    t = track(raw)
    result["utterance_pitch_track"] = t.model_dump(mode="json")
    before = copy.deepcopy(result)
    loaded = load_pitch_track(
        result, audio_sha256="a" * 64, tracker_source="changed", tracker_version="99", parameters={}
    )
    assert loaded == t and result == before
    with pytest.raises(ValueError):
        load_pitch_track(
            result, audio_sha256="b" * 64, tracker_source="same", tracker_version="1", parameters={}
        )


def test_real_praat_extraction_is_once_for_transcripts_targets_and_empty_metadata(
    uploaded_utterance,
    session_factory,
    store,
):
    analyzer = PraatAcousticAnalyzer()
    spy = Mock(wraps=analyzer.analyze)
    analyzer.analyze = spy
    with session_factory() as db:
        u = db.get(Utterance, uuid.UUID(uploaded_utterance["id"]))
        asset = db.get(AudioAsset, u.canonical_audio_asset_id)
        assert hashlib.sha256(store.read(asset.storage_key)).hexdigest() == asset.sha256
        snapshots, run_ids = [], []
        for text, target in [("贵州", None), ("鬼粥", "广州"), ("另一个", "完全不同"), ("", None)]:
            # Linguistic resolution is downstream and cannot enter this service API.
            units = perceived_syllables(text, {})
            for unit in units:
                unit.lexical_tone = 4 if target else 1
            run = AcousticAnalysisService(db, store, analyzer).run(
                account_id=u.account_id, utterance_id=u.id
            )
            snapshots.append(run.normalized_result["utterance_pitch_track"])
            run_ids.append(run.id)
        assert spy.call_count == 1 and len(set(run_ids)) == 1
        assert all(s == snapshots[0] for s in snapshots)
        assert db.scalar(select(func.count()).select_from(AcousticRun)) == 1
        assert snapshots[0]["audio_sha256"] == asset.sha256


SAVED = json.loads((Path(__file__).parent / "fixtures/utterance_pitch_evidence.json").read_text())


@pytest.mark.parametrize("row", SAVED, ids=lambda r: r["id"])
def test_saved_failure_set_and_negative_controls(row):
    t = track(row["f0"], row["duration_seconds"])
    for w in row["windows"]:
        e = eligibility(t, w["start"], w["end"])
        if row["id"] in {"take_1", "take_3"} and w["label"] == "苹":
            assert e.state == "incomplete" and e.metrics.missing_tail_seconds >= 0.14
        if row["id"] in {"take_2", "human_control"} and w["label"] == "苹":
            assert e.state == "sufficient"
        if row["id"] == "f5dc0cc1" and w["label"] == "州":
            assert e.metrics.maximum_raw_jump_semitones > 21
        if row["negative"]:
            # Local coherence is NOT speech presence or comparison permission.
            assert perceived_syllables("要", {})[0].tone_comparison_policy == "experimental"
            observed = classify_contour(
                display_from_track(t), w["start"], w["end"], raw=row["f0"], pitch_track=t
            )
            assert gate_observation(observed, e).classification == "unclear"


def test_distinct_persisted_perceptions_reuse_the_same_track(
    uploaded_utterance, session_factory, store, settings
):
    from test_perceived_speech import perception_for

    from benma_api.pronunciation.alignment import DisabledAligner
    from benma_api.pronunciation.perceived import PerceivedSpeechAnalysisService

    analyzer = PraatAcousticAnalyzer()
    spy = Mock(wraps=analyzer.analyze)
    analyzer.analyze = spy
    snapshots = []
    for text in ["贵州", "鬼粥"]:
        perception = perception_for(session_factory, uploaded_utterance, text)
        with session_factory() as db:
            run = PerceivedSpeechAnalysisService(
                db, store, settings, analyzer=analyzer, aligner=DisabledAligner()
            ).run(account_id=perception.account_id, perception_run_id=perception.id)
            acoustic = db.get(AcousticRun, run.acoustic_run_id)
            snapshots.append((acoustic.id, acoustic.normalized_result["utterance_pitch_track"]))
    assert spy.call_count == 1
    assert snapshots[0] == snapshots[1]


def test_adjacent_regions_punctuation_and_final_frame_have_exact_ownership():
    t = track(coherent())
    units = perceived_syllables("贵州。", {})
    assert [u.characters for u in units] == ["贵", "州"]
    first = project_pitch(t, 0, 0.25, timing_source="saved_grapheme")
    final = project_pitch(t, 0.25, 0.5, timing_source="saved_grapheme")
    assert first.frame_indices == tuple(range(25))
    assert final.frame_indices == tuple(range(25, 50))
    assert set(first.frame_indices).isdisjoint(final.frame_indices)
    assert t.frames[final.frame_indices[-1]].timestamp_seconds == 0.49
    assert not project_pitch(t, None, None, timing_source=None).frame_indices


def test_track_contract_forbids_linguistic_identity_and_digest_is_deterministic():
    a, b = track(coherent()), track(coherent())
    assert a == b and a.evidence_id == b.evidence_id
    for name in ["transcript", "characters", "pinyin", "target", "lexical_tone", "surface_tone"]:
        with pytest.raises(ValidationError):
            UtterancePitchTrack.model_validate({**a.model_dump(), name: "arbitrary metadata"})

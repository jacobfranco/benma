from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from benchmark.annotations import commit_blind, commit_revealed, load_annotation, verify_blind
from benchmark.models import BlindListenerResponse, RaterProfile, RevealedTargetResponse


def blind_response() -> BlindListenerResponse:
    return BlindListenerResponse(
        perceived_text="背景",
        understood_first_pass=False,
        would_request_repetition=True,
        confidence=0.7,
    )


def revealed_response() -> RevealedTargetResponse:
    return RevealedTargetResponse(
        tone_problem=True,
        affected_syllable_indices=(1,),
        initial_problem=False,
        final_problem=False,
        rhythm_or_prosody_issue=False,
        still_understandable=False,
        severity="moderate",
    )


def test_blind_commit_is_hashed_and_immutable(tmp_path: Path) -> None:
    path = tmp_path / "blind.json"
    commit = commit_blind(
        path,
        annotation_id="a1",
        sample_id="sample_1",
        listener_id="listener_1",
        randomized_order=3,
        response=blind_response(),
        now=datetime(2026, 8, 3, tzinfo=UTC),
    )
    assert verify_blind(commit)
    with pytest.raises(FileExistsError, match="immutable"):
        commit_blind(
            path,
            annotation_id="a1",
            sample_id="sample_1",
            listener_id="listener_1",
            randomized_order=3,
            response=blind_response(),
        )


def test_reveal_references_committed_blind_hash(tmp_path: Path) -> None:
    blind = tmp_path / "blind.json"
    reveal = tmp_path / "reveal.json"
    commit = commit_blind(
        blind,
        annotation_id="a1",
        sample_id="sample_1",
        listener_id="listener_1",
        randomized_order=0,
        response=blind_response(),
    )
    annotation = commit_revealed(blind, reveal, response=revealed_response())
    assert annotation.revealed
    assert annotation.revealed.blind_commit_sha256 == commit.commit_sha256
    assert load_annotation(blind, reveal) == annotation


def test_reveal_rejects_tampered_blind_content(tmp_path: Path) -> None:
    blind = tmp_path / "blind.json"
    reveal = tmp_path / "reveal.json"
    commit_blind(
        blind,
        annotation_id="a1",
        sample_id="sample_1",
        listener_id="listener_1",
        randomized_order=0,
        response=blind_response(),
    )
    payload = json.loads(blind.read_text(encoding="utf-8"))
    payload["response"]["perceived_text"] = "北京"
    blind.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="no longer matches"):
        commit_revealed(blind, reveal, response=revealed_response())


def test_revealed_commit_is_create_only(tmp_path: Path) -> None:
    blind = tmp_path / "blind.json"
    reveal = tmp_path / "reveal.json"
    commit_blind(
        blind,
        annotation_id="a1",
        sample_id="sample_1",
        listener_id="listener_1",
        randomized_order=0,
        response=blind_response(),
    )
    commit_revealed(blind, reveal, response=revealed_response())
    with pytest.raises(FileExistsError, match="immutable"):
        commit_revealed(blind, reveal, response=revealed_response())


def test_listener_cannot_rate_same_sample_twice(tmp_path: Path) -> None:
    directory = tmp_path / "blind"
    commit_blind(
        directory / "first.json",
        annotation_id="a1",
        sample_id="sample_1",
        listener_id="listener_1",
        randomized_order=0,
        response=blind_response(),
    )
    with pytest.raises(ValueError, match="already annotated"):
        commit_blind(
            directory / "second.json",
            annotation_id="a2",
            sample_id="sample_1",
            listener_id="listener_1",
            randomized_order=1,
            response=blind_response(),
        )


def test_profile_must_match_listener(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="profile ID"):
        commit_blind(
            tmp_path / "blind" / "a1.json",
            annotation_id="a1",
            sample_id="sample_1",
            listener_id="listener_1",
            randomized_order=0,
            response=blind_response(),
            rater_profile=RaterProfile(
                rater_id="listener_2", native_mandarin_self_report=True
            ),
        )

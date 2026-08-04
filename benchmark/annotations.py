"""Append-only two-stage human annotation commits."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from benchmark.models import (
    BlindAnnotationCommit,
    BlindListenerResponse,
    HumanListenerAnnotation,
    RaterProfile,
    RevealedAnnotationCommit,
    RevealedTargetResponse,
)
from benchmark.storage import load_model, write_model


def _blind_digest(
    *,
    sample_id: str,
    listener_id: str,
    randomized_order: int,
    response: BlindListenerResponse,
    rater_profile: RaterProfile | None,
) -> str:
    payload: dict[str, object] = {
        "sample_id": sample_id,
        "listener_id": listener_id,
        "randomized_order": randomized_order,
        "response": response.model_dump(mode="json", exclude_none=True),
    }
    if rater_profile is not None:
        payload["rater_profile"] = rater_profile.model_dump(mode="json", exclude_none=True)
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def commit_blind(
    path: Path,
    *,
    annotation_id: str,
    sample_id: str,
    listener_id: str,
    randomized_order: int,
    response: BlindListenerResponse,
    rater_profile: RaterProfile | None = None,
    now: datetime | None = None,
) -> BlindAnnotationCommit:
    if path.exists():
        raise FileExistsError("blind responses are immutable; create a new annotation ID")
    for existing_path in path.parent.glob("*.json"):
        existing = load_model(existing_path, BlindAnnotationCommit)
        if existing.sample_id == sample_id and existing.listener_id == listener_id:
            raise ValueError("this rater already annotated this sample")
    if rater_profile is not None and rater_profile.rater_id != listener_id:
        raise ValueError("rater profile ID must match listener ID")
    commit = BlindAnnotationCommit(
        annotation_id=annotation_id,
        sample_id=sample_id,
        listener_id=listener_id,
        rater_profile=rater_profile,
        randomized_order=randomized_order,
        response=response,
        committed_at=now or datetime.now(UTC),
        commit_sha256=_blind_digest(
            sample_id=sample_id,
            listener_id=listener_id,
            randomized_order=randomized_order,
            response=response,
            rater_profile=rater_profile,
        ),
    )
    write_model(path, commit)
    return commit


def verify_blind(commit: BlindAnnotationCommit) -> bool:
    return commit.commit_sha256 == _blind_digest(
        sample_id=commit.sample_id,
        listener_id=commit.listener_id,
        randomized_order=commit.randomized_order,
        response=commit.response,
        rater_profile=commit.rater_profile,
    )


def commit_revealed(
    blind_path: Path,
    revealed_path: Path,
    *,
    response: RevealedTargetResponse,
    now: datetime | None = None,
) -> HumanListenerAnnotation:
    if revealed_path.exists():
        raise FileExistsError("revealed responses are immutable; create a new annotation ID")
    blind = load_model(blind_path, BlindAnnotationCommit)
    if not verify_blind(blind):
        raise ValueError("blind response content no longer matches its commit hash")
    revealed = RevealedAnnotationCommit(
        annotation_id=blind.annotation_id,
        sample_id=blind.sample_id,
        listener_id=blind.listener_id,
        blind_commit_sha256=blind.commit_sha256,
        response=response,
        committed_at=now or datetime.now(UTC),
    )
    annotation = HumanListenerAnnotation(blind=blind, revealed=revealed)
    write_model(revealed_path, revealed)
    return annotation


def load_annotation(blind_path: Path, revealed_path: Path | None = None) -> HumanListenerAnnotation:
    blind = load_model(blind_path, BlindAnnotationCommit)
    revealed = None
    if revealed_path is not None and revealed_path.exists():
        revealed = load_model(revealed_path, RevealedAnnotationCommit)
    return HumanListenerAnnotation(blind=blind, revealed=revealed)

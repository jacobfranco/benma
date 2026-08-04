from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmark.annotation_workbench import WORKBENCH_HTML, AnnotationWorkbench
from benchmark.models import (
    BlindListenerResponse,
    CorpusManifest,
    ListenerRole,
    RaterProfile,
    RevealedTargetResponse,
)


def _manifest(recorded_sample) -> CorpusManifest:  # type: ignore[no-untyped-def]
    return CorpusManifest(
        corpus_id="workbench-test",
        corpus_version="v1",
        desired_sample_count=1,
        description="test",
        samples=(recorded_sample,),
    )


def _profile() -> RaterProfile:
    return RaterProfile(
        rater_id="listener_1",
        native_mandarin_self_report=True,
        role=ListenerRole.ORDINARY_NATIVE_LISTENER,
    )


def _blind() -> BlindListenerResponse:
    return BlindListenerResponse(
        perceived_text="你好",
        perceived_pinyin=("nǐ", "hǎo"),
        understood_first_pass=True,
        would_request_repetition=False,
        confidence=0.9,
    )


def _revealed() -> RevealedTargetResponse:
    return RevealedTargetResponse(
        tone_problem=False,
        initial_problem=False,
        final_problem=False,
        rhythm_or_prosody_issue=False,
        still_understandable=True,
        severity="none",
    )


def test_blind_package_hides_target_and_reveal_requires_commit(
    tmp_path: Path, recorded_sample  # type: ignore[no-untyped-def]
) -> None:
    workbench = AnnotationWorkbench(_manifest(recorded_sample), tmp_path / "annotations", seed="s")
    item = workbench.next_blind_item("listener_1")
    assert item is not None
    serialized = json.dumps(item)
    assert recorded_sample.sample_id not in serialized
    assert recorded_sample.intended_text not in serialized
    assert "pinyin" not in serialized
    assert (
        workbench.audio_path(item["item_token"], "listener_1")
        == recorded_sample.audio.asset_path
    )

    reveal = workbench.commit_blind_stage(
        item["item_token"],
        listener_id="listener_1",
        profile=_profile(),
        response=_blind(),
    )
    assert reveal["target"] == "你好"
    assert reveal["pinyin"] == ("nǐ", "hǎo")
    with pytest.raises(PermissionError, match="expired"):
        workbench.audio_path(item["item_token"], "listener_1")
    workbench.commit_revealed_stage(
        reveal["reveal_token"], listener_id="listener_1", response=_revealed()
    )
    assert workbench.next_blind_item("listener_1") is None


def test_annotation_bundle_round_trip_is_create_only(
    tmp_path: Path, recorded_sample  # type: ignore[no-untyped-def]
) -> None:
    source = AnnotationWorkbench(_manifest(recorded_sample), tmp_path / "source", seed="s")
    item = source.next_blind_item("listener_1")
    assert item is not None
    reveal = source.commit_blind_stage(
        item["item_token"],
        listener_id="listener_1",
        profile=_profile(),
        response=_blind(),
    )
    source.commit_revealed_stage(
        reveal["reveal_token"], listener_id="listener_1", response=_revealed()
    )
    bundle = tmp_path / "annotations.zip"
    source.export_bundle(bundle)
    imported = AnnotationWorkbench(_manifest(recorded_sample), tmp_path / "imported", seed="s")
    assert imported.import_bundle(bundle) == (1, 1)
    with pytest.raises(FileExistsError, match="create-only"):
        imported.import_bundle(bundle)


def test_workbench_html_contains_local_recovery_and_two_stages() -> None:
    assert "localStorage" in WORKBENCH_HTML
    assert "Stage A" in WORKBENCH_HTML
    assert "Stage B" in WORKBENCH_HTML
    assert "provider" not in WORKBENCH_HTML.lower()

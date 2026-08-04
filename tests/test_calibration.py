from __future__ import annotations

from pathlib import Path

import pytest

from benchmark.annotations import commit_blind, commit_revealed
from benchmark.evaluation.calibration import (
    BinaryObservation,
    consensus_for_sample,
    create_stratified_split,
    explore_thresholds,
    persist_split,
    rate_estimate,
)
from benchmark.models import (
    BenchmarkSample,
    BlindListenerResponse,
    CalibrationMode,
    CalibrationSplitManifest,
    HumanListenerAnnotation,
    ListenerRole,
    RaterProfile,
    RecordingQualityEvidence,
    RevealedTargetResponse,
)


def _annotations(
    root: Path,
    sample: BenchmarkSample,
    *,
    tone_problem: bool,
    affected: tuple[int, ...] = (),
    produced_tones: tuple[str, ...] = (),
    invalid: bool = False,
) -> list[HumanListenerAnnotation]:
    annotations = []
    for index in range(3):
        listener = f"native_{index}"
        blind_path = root / "blind" / f"ann_{index}.json"
        revealed_path = root / "revealed" / f"ann_{index}.json"
        commit_blind(
            blind_path,
            annotation_id=f"ann_{index}",
            sample_id=sample.sample_id,
            listener_id=listener,
            randomized_order=index,
            rater_profile=RaterProfile(
                rater_id=listener,
                native_mandarin_self_report=True,
                role=ListenerRole.ORDINARY_NATIVE_LISTENER,
            ),
            response=BlindListenerResponse(
                perceived_text=sample.intended_text or "",
                understood_first_pass=not invalid,
                would_request_repetition=invalid,
                confidence=0.9,
            ),
        )
        annotations.append(
            commit_revealed(
                blind_path,
                revealed_path,
                response=RevealedTargetResponse(
                    tone_problem=tone_problem,
                    affected_syllable_indices=affected,
                    initial_problem=False,
                    final_problem=False,
                    rhythm_or_prosody_issue=False,
                    still_understandable=not invalid,
                    severity="severe" if invalid else "minor" if tone_problem else "none",
                    perceived_produced_tones=produced_tones,
                    invalid_sample=invalid,
                ),
            )
        )
    return annotations


def test_rate_estimate_preserves_counts_and_wilson_interval() -> None:
    estimate = rate_estimate(2, 10)
    assert estimate.numerator == 2
    assert estimate.denominator == 10
    assert estimate.fraction == pytest.approx(0.2)
    assert estimate.confidence_interval_95 is not None
    low, high = estimate.confidence_interval_95
    assert low < 0.2 < high
    assert rate_estimate(0, 0).fraction is None


def test_consensus_uses_native_raters_and_affected_syllables_not_intent(
    tmp_path: Path, recorded_sample: BenchmarkSample
) -> None:
    sample = recorded_sample.model_copy(
        update={"calibration_mode": CalibrationMode.LEARNER_INTENTIONAL_TONE_ERROR}
    )
    annotations = _annotations(
        tmp_path,
        sample,
        tone_problem=True,
        affected=(1,),
        produced_tones=("T2", "T4"),
    )
    consensus = consensus_for_sample(sample, annotations)
    assert consensus["qualifying_native_listener_count"] == 3
    assert consensus["tone_issue"]["majority"] is True
    assert consensus["human_supported_tone_error_indices"] == [1]
    assert consensus["human_supported_produced_tones"] == {"0": "T2", "1": "T4"}

    acceptable = consensus_for_sample(
        sample,
        _annotations(tmp_path / "acceptable", sample, tone_problem=False),
    )
    assert acceptable["consensus_class"] == "strong_accept"
    assert acceptable["human_supported_tone_error_indices"] == []


def test_recording_quality_can_invalidate_consensus(
    tmp_path: Path, recorded_sample: BenchmarkSample
) -> None:
    sample = recorded_sample.model_copy(
        update={"recording_quality": RecordingQualityEvidence(status="invalid")}
    )
    consensus = consensus_for_sample(
        sample, _annotations(tmp_path, sample, tone_problem=False)
    )
    assert consensus["consensus_class"] == "invalid_sample"


def test_split_is_deterministic_disjoint_and_immutable(
    tmp_path: Path, recorded_sample: BenchmarkSample
) -> None:
    samples = [
        recorded_sample.model_copy(
            update={
                "sample_id": f"sample_{index}",
                "calibration_mode": (
                    CalibrationMode.LEARNER_CORRECT
                    if index < 4
                    else CalibrationMode.NATIVE_CONTROL
                ),
            }
        )
        for index in range(8)
    ]
    first = create_stratified_split(samples, benchmark_version="v1", split_version="split-a")
    second = create_stratified_split(samples, benchmark_version="v1", split_version="split-a")
    assert first.calibration_sample_ids == second.calibration_sample_ids
    assert first.held_out_sample_ids == second.held_out_sample_ids
    assert set(first.calibration_sample_ids).isdisjoint(first.held_out_sample_ids)
    path = tmp_path / "split.json"
    persisted = persist_split(path, first)
    assert persist_split(path, second) == persisted
    changed = CalibrationSplitManifest(
        benchmark_version="v1",
        split_version="split-a",
        calibration_sample_ids=first.held_out_sample_ids,
        held_out_sample_ids=first.calibration_sample_ids,
    )
    with pytest.raises(ValueError, match="immutable"):
        persist_split(path, changed)


def test_thresholds_are_selected_on_calibration_and_report_holdout_separately() -> None:
    split = CalibrationSplitManifest(
        benchmark_version="v1",
        split_version="s1",
        calibration_sample_ids=("cal-error", "cal-ok"),
        held_out_sample_ids=("hold-error", "hold-ok"),
    )
    candidates = explore_thresholds(
        [
            BinaryObservation("cal-error", 30, True),
            BinaryObservation("cal-ok", 90, False),
            BinaryObservation("hold-error", 95, True),
            BinaryObservation("hold-ok", 10, False),
        ],
        split=split,
    )
    assert candidates
    assert all(candidate["promotion_state"] == "exploratory_only" for candidate in candidates)
    assert all(
        candidate["calibration"]["false_acceptance"]["denominator"] == 1
        for candidate in candidates
    )
    assert all(
        candidate["held_out"]["false_acceptance"]["denominator"] == 1
        for candidate in candidates
    )

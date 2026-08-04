from __future__ import annotations

from pathlib import Path

from benchmark.annotations import commit_blind, commit_revealed
from benchmark.models import (
    BenchmarkSample,
    BlindListenerResponse,
    CalibrationMode,
    CorpusManifest,
    EvidenceOrigin,
    KnownTargetAssessmentResult,
    ProviderRun,
    RaterProfile,
    RequestMode,
    RevealedTargetResponse,
    RunStatus,
    SpeakerCategory,
    SyllableAssessment,
)
from benchmark.reports.pronunciation_calibration import generate_pronunciation_calibration
from benchmark.storage import write_model


def _three_annotations(
    root: Path,
    sample: BenchmarkSample,
    *,
    prefix: str,
    tone_problem: bool,
    affected: tuple[int, ...] = (),
    tones: tuple[str, ...] = (),
) -> None:
    for index in range(3):
        listener = f"{prefix}_native_{index}"
        annotation_id = f"{prefix}_ann_{index}"
        blind = root / "blind" / f"{annotation_id}.json"
        commit_blind(
            blind,
            annotation_id=annotation_id,
            sample_id=sample.sample_id,
            listener_id=listener,
            randomized_order=index,
            rater_profile=RaterProfile(
                rater_id=listener, native_mandarin_self_report=True
            ),
            response=BlindListenerResponse(
                perceived_text=sample.intended_text or "",
                understood_first_pass=True,
                would_request_repetition=False,
                confidence=0.9,
            ),
        )
        commit_revealed(
            blind,
            root / "revealed" / f"{annotation_id}.json",
            response=RevealedTargetResponse(
                tone_problem=tone_problem,
                affected_syllable_indices=affected,
                initial_problem=False,
                final_problem=False,
                rhythm_or_prosody_issue=False,
                still_understandable=True,
                severity="minor" if tone_problem else "none",
                perceived_produced_tones=tones,
            ),
        )


def _run(
    sample: BenchmarkSample,
    result: KnownTargetAssessmentResult,
    *,
    configuration: dict[str, str] | None = None,
) -> ProviderRun:
    return ProviderRun(
        run_id=f"run-{sample.sample_id}-{(configuration or {}).get('mode', 'baseline')}",
        provider="live_test_provider",
        product="mandarin_product",
        adapter_version="1",
        benchmark_sample_id=sample.sample_id,
        request_mode=RequestMode.KNOWN_TARGET,
        request_configuration=configuration or {},
        normalized_result=result,
        raw_response={"capture_type": "LIVE_PROVIDER_RESPONSE"},
        evidence_origin=EvidenceOrigin.LIVE_PROVIDER,
        status=RunStatus.SUCCEEDED,
    )


def test_calibration_report_excludes_synthetic_and_states_exact_deficit(
    tmp_path: Path, recorded_sample: BenchmarkSample
) -> None:
    synthetic = recorded_sample.model_copy(
        update={
            "sample_id": "synthetic_reference",
            "speaker_category": SpeakerCategory.SYNTHETIC_REFERENCE,
        }
    )
    manifest = CorpusManifest(
        corpus_id="pilot",
        corpus_version="test",
        desired_sample_count=50,
        description="test",
        samples=(synthetic,),
    )
    manifest_path = tmp_path / "manifest.json"
    write_model(manifest_path, manifest)
    output = tmp_path / "output"
    summary = generate_pronunciation_calibration(
        manifest_path=manifest_path,
        runs_dir=tmp_path / "runs",
        annotations_dir=tmp_path / "annotations",
        output_dir=output,
    )
    assert summary["counts"]["real_recordings"] == 0
    assert summary["calibration_ready"] is False
    assert summary["gates"]["learner_deliberate_errors"] == {
        "ready": False,
        "actual": 0,
        "required": 30,
    }
    assert (output / "pronunciation-calibration.json").exists()
    report = (output / "pronunciation-calibration.md").read_text(encoding="utf-8")
    assert "NOT READY" in report
    assert "Categorical pronunciation calibration remains incomplete" in report


def test_report_uses_surface_tones_human_error_indices_and_explicit_denominators(
    tmp_path: Path, recorded_sample: BenchmarkSample
) -> None:
    error_sample = recorded_sample.model_copy(
        update={
            "sample_id": "human_error",
            "calibration_mode": CalibrationMode.LEARNER_INTENTIONAL_TONE_ERROR,
        }
    )
    acceptable_sample = recorded_sample.model_copy(
        update={
            "sample_id": "human_acceptable",
            "calibration_mode": CalibrationMode.LEARNER_CORRECT,
        }
    )
    manifest = CorpusManifest(
        corpus_id="pilot",
        corpus_version="test",
        desired_sample_count=2,
        description="test",
        samples=(error_sample, acceptable_sample),
    )
    manifest_path = tmp_path / "manifest.json"
    write_model(manifest_path, manifest)
    annotations = tmp_path / "annotations"
    _three_annotations(
        annotations,
        error_sample,
        prefix="error",
        tone_problem=True,
        affected=(1,),
        tones=("T2", "T4"),
    )
    _three_annotations(
        annotations,
        acceptable_sample,
        prefix="acceptable",
        tone_problem=False,
        tones=("T2", "T3"),
    )
    provider_result = KnownTargetAssessmentResult(
        syllables=(
            SyllableAssessment(reference_tone="T3", detected_tone="T2", tone_score=90),
            SyllableAssessment(reference_tone="T3", detected_tone="T3", tone_score=90),
        )
    )
    runs = tmp_path / "runs"
    write_model(runs / "error.json", _run(error_sample, provider_result))
    write_model(runs / "acceptable.json", _run(acceptable_sample, provider_result))
    missing_hypothesis = KnownTargetAssessmentResult(
        syllables=(SyllableAssessment(), SyllableAssessment())
    )
    write_model(
        runs / "missing.json",
        _run(error_sample, missing_hypothesis, configuration={"mode": "missing"}),
    )
    summary = generate_pronunciation_calibration(
        manifest_path=manifest_path,
        runs_dir=runs,
        annotations_dir=annotations,
        output_dir=tmp_path / "output",
    )
    identity = next(iter(summary["provider_metrics"]))
    assert identity.startswith("live_test_provider/mandarin_product#config-")
    metrics = summary["provider_metrics"][identity]
    assert metrics["tone_detection_false_acceptance"] == {
        "numerator": 1,
        "denominator": 1,
        "fraction": 1.0,
        "confidence_interval_95": metrics["tone_detection_false_acceptance"][
            "confidence_interval_95"
        ],
    }
    assert metrics["acceptable_tone_false_rejection"]["numerator"] == 0
    assert metrics["acceptable_tone_false_rejection"]["denominator"] == 2
    assert summary["gate_sets"]["categorical_tone"][
        "human_supported_tone_error_syllables"
    ]["actual"] == 1
    assert summary["categorical_tone_judgment_allowed"] is False
    missing_metrics = next(
        value
        for key, value in summary["provider_metrics"].items()
        if key != identity
    )
    assert missing_metrics["tone_error_abstentions"] == 1
    assert missing_metrics["tone_detection_false_acceptance"]["denominator"] == 0

from __future__ import annotations

from pathlib import Path

from benchmark.models import BenchmarkSample, CorpusManifest, SpeakerCategory
from benchmark.reports.pronunciation_calibration import generate_pronunciation_calibration
from benchmark.storage import write_model


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

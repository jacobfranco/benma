from __future__ import annotations

from pathlib import Path

from benchmark.fixtures import materialize_replay_fixtures
from benchmark.reports.generation import generate_report

ROOT = Path(__file__).resolve().parents[1]


def generate(tmp_path: Path) -> dict[str, object]:
    fixtures = tmp_path / "fixtures"
    materialize_replay_fixtures(fixtures)
    return generate_report(
        manifest_path=ROOT / "benchmark/corpus/manifests/benma-v0.1.0.json",
        runs_dir=fixtures / "runs",
        annotations_dir=fixtures / "annotations",
        pricing_path=ROOT / "benchmark/evaluation/cost/pricing-v2026-08-03.json",
        capabilities_path=ROOT / "benchmark/reports/templates/provider-capabilities.json",
        output_dir=tmp_path / "outputs",
    )


def test_report_is_explicitly_fixture_only(tmp_path: Path) -> None:
    summary = generate(tmp_path)
    report = (tmp_path / "outputs/report.md").read_text(encoding="utf-8")
    assert summary["data_status"] == "replay_fixture_only"
    assert "must not be used" in report
    assert "No provider winner is declared" in report


def test_report_contains_failure_gallery_and_scorecards(tmp_path: Path) -> None:
    summary = generate(tmp_path)
    assert summary["failure_gallery"]
    assert summary["provider_capabilities"]
    assert "openai/gpt-4o-transcribe/context_probe" in summary["unknown_target"]
    assert (
        summary["known_target"]["azure_speech/pronunciation_assessment_zh-CN"][
            "tone_false_accept_rate"
        ]
        is None
    )
    report = (tmp_path / "outputs/report.md").read_text(encoding="utf-8")
    assert "sentence_beijing_wrong_tone" in report
    assert "Tone false accept" in report
    assert "Tone confusion matrices" in report
    assert "Negative/control behavior" in report
    assert "Explicitly unavailable" in report


def test_report_generation_is_deterministic(tmp_path: Path) -> None:
    generate(tmp_path)
    first = {
        path.name: path.read_bytes() for path in (tmp_path / "outputs").iterdir() if path.is_file()
    }
    generate(tmp_path)
    second = {
        path.name: path.read_bytes() for path in (tmp_path / "outputs").iterdir() if path.is_file()
    }
    assert first == second


def test_fixture_raw_response_survives_report_pipeline(tmp_path: Path) -> None:
    fixtures = tmp_path / "fixtures"
    materialize_replay_fixtures(fixtures)
    run_path = fixtures / "runs/fixture-unknown-funasr-sentence_beijing_wrong_tone.json"
    before = run_path.read_bytes()
    generate_report(
        manifest_path=ROOT / "benchmark/corpus/manifests/benma-v0.1.0.json",
        runs_dir=fixtures / "runs",
        annotations_dir=fixtures / "annotations",
        pricing_path=ROOT / "benchmark/evaluation/cost/pricing-v2026-08-03.json",
        capabilities_path=ROOT / "benchmark/reports/templates/provider-capabilities.json",
        output_dir=tmp_path / "outputs",
    )
    assert run_path.read_bytes() == before

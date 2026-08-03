from __future__ import annotations

import statistics
from pathlib import Path

import pytest
from conftest import write_wav

from benchmark.acoustics.alignment import parse_textgrid
from benchmark.acoustics.pitch import AutocorrelationPitchAnalyzer
from benchmark.acoustics.plot import write_diagnostic_svg


def test_autocorrelation_tracks_synthetic_pitch(canonical_wav: Path) -> None:
    result = AutocorrelationPitchAnalyzer().analyze(str(canonical_wav))
    values = [point.f0_hz for point in result.f0 if point.f0_hz is not None]
    assert values
    assert statistics.median(values) == pytest.approx(200, rel=0.04)
    assert result.normalization_method
    assert result.contour_features["voiced_fraction"] > 0.8


def test_silence_remains_unvoiced(tmp_path: Path) -> None:
    silent = write_wav(tmp_path / "silent.wav", amplitude=0.0)
    result = AutocorrelationPitchAnalyzer().analyze(str(silent))
    assert result.f0
    assert all(point.f0_hz is None for point in result.f0)
    assert result.contour_features["voiced_fraction"] == 0.0


def test_static_svg_contains_waveform_and_f0(canonical_wav: Path, tmp_path: Path) -> None:
    result = AutocorrelationPitchAnalyzer().analyze(str(canonical_wav))
    output = tmp_path / "plot.svg"
    write_diagnostic_svg(canonical_wav, result, output, title="T1 diagnostic")
    text = output.read_text(encoding="utf-8")
    assert "<svg" in text
    assert "T1 diagnostic" in text
    assert "normalized_autocorrelation" in text


def test_textgrid_parser_extracts_nonempty_intervals(tmp_path: Path) -> None:
    grid = tmp_path / "test.TextGrid"
    grid.write_text(
        """File type = \"ooTextFile\"\n"
        "intervals [1]:\n    xmin = 0\n    xmax = 0.4\n    text = \"你\"\n"
        "intervals [2]:\n    xmin = 0.4\n    xmax = 0.8\n    text = \"好\"\n""",
        encoding="utf-8",
    )
    units = parse_textgrid(grid)
    assert [unit.label for unit in units] == ["你", "好"]
    assert units[1].span.start_seconds == 0.4

from __future__ import annotations

from pathlib import Path

from benchmark.acoustics.calibration import materialize_acoustic_calibrations


def test_acoustic_calibrations_are_labeled_and_complete(tmp_path: Path) -> None:
    assert materialize_acoustic_calibrations(tmp_path) == 8
    assert len(list(tmp_path.glob("*.wav"))) == 8
    assert len(list(tmp_path.glob("*.json"))) == 8
    assert len(list(tmp_path.glob("*.svg"))) == 8
    for plot in tmp_path.glob("*.svg"):
        assert "SYNTHETIC CALIBRATION" in plot.read_text(encoding="utf-8")

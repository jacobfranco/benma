"""Exact offline re-selection contract; no private audio or provider dependency."""

import json

from benchmark.pronunciation_v2.pitch_robustness_replay import FIXTURE, ROOT, replay


def test_physical_reselection_reproduces_published_ui_without_mutating_saved_history():
    saved = json.loads(FIXTURE.read_text())
    expected = json.loads(
        (ROOT / "apps/mobile/src/__tests__/fixtures/pitchRobustnessPhysical.json").read_text()
    )
    original = json.dumps(saved)
    for fixture, published in zip(saved, expected, strict=True):
        result = replay(fixture)
        assert result["analysis"] == published
        assert all(
            f["selected_f0_hz"] == f["raw_f0_hz"]
            for f in result["track"]["frames"]
            if f["selected_f0_hz"]
        )
    assert json.dumps(saved) == original

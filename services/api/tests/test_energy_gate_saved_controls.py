"""Replay existing selections; no new tracker execution or lowered threshold."""

import copy
import json
from pathlib import Path

import pytest

from benma_api.pronunciation.pitch_evidence import build_pitch_track

ROWS = {
    r["id"]: r
    for r in json.loads(
        (Path(__file__).parent / "fixtures/energy_gate_saved_controls.json").read_text()
    )
}


def track(row):
    return build_pitch_track(
        dict(f0=row["f0"], duration_seconds=row["duration"]),
        audio_sha256="saved-fixture",
        tracker_source="saved-praat",
        tracker_version="unchanged",
        parameters={},
    )


def test_weak_ge_raw_estimates_remain_visible_in_history_but_all_are_energy_excluded():
    row = ROWS["89cee47e:个"]
    frozen = copy.deepcopy(row)
    raw = [p for p in row["f0"] if p["tracker_f0_hz"]]
    assert len(raw) == 8
    assert row["threshold"] == pytest.approx(0.006968468060966106)
    assert all(p["energy_rms"] < row["threshold"] and p["energy_gated"] for p in raw)
    saved = track(row)
    assert sum(f.raw_f0_hz is not None for f in saved.frames) == 8
    assert all(f.selected_f0_hz is None for f in saved.frames)
    assert all("below_energy_gate" in f.exclusion_reasons for f in saved.frames if f.raw_f0_hz)
    assert row == frozen


@pytest.mark.parametrize(
    "name,selected", [("89cee47e:我", 41), ("4b9dbd2b:个", 22), ("8faf1a90:个", 31)]
)
def test_strong_and_neutral_voiced_controls_keep_their_saved_support(name, selected):
    row = ROWS[name]
    t = track(row)
    assert sum(f.selected_f0_hz is not None for f in t.frames) == selected
    # The evidence builder receives no lexical/neutral identity.
    assert track({**row, "id": "arbitrary-character"}).frames == t.frames


@pytest.mark.parametrize("name", ["neg_digital_silence", "neg_stationary_noise", "neg_clicks"])
def test_saved_unvoiced_negative_controls_do_not_grow_pitch(name):
    t = track(ROWS[name])
    assert all(f.raw_f0_hz is None and f.selected_f0_hz is None for f in t.frames)


def test_periodic_nonspeech_is_a_counterexample_to_coherence_alone():
    row = ROWS["silence_periodic"]
    raw = [p for p in row["f0"] if 0.98 < p["timestamp_seconds"] < 1.06]
    assert len(raw) == 8
    assert all(p["tracker_f0_hz"] and p["energy_gated"] and p["quality_usable"] for p in raw)
    assert all(p["voicing_probability"] > 0.5 for p in raw)
    # Coherent raw background exists; do not promote it merely because it is periodic.
    t = track(row)
    assert all(f.selected_f0_hz is None for f in t.frames if 0.98 < f.timestamp_seconds < 1.06)


def test_low_f0_control_is_not_misattributed_to_the_energy_gate():
    row = ROWS["syn_steady_70"]
    voiced = [p for p in row["f0"] if p["tracker_f0_hz"]]
    assert len(voiced) == 159
    assert not any(p["energy_gated"] for p in voiced)
    assert all(p["energy_rms"] >= row["threshold"] for p in voiced)
    assert any(not p["quality_usable"] for p in voiced)
    # The existing low-frequency quality rejection remains a separately documented limitation.
    assert sum(f.selected_f0_hz is not None for f in track(ROWS["syn_steady_110"]).frames) == 161

"""Research-only frozen-corpus regression; no downloads or production behavior."""

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pytest

from benchmark.pronunciation_v2.f0_foundation import known_f0_metrics, track_record
from benchmark.pronunciation_v2.f0_foundation_rmvpe import (
    BIN_HZ,
    ROOT,
    SWEEP_THRESHOLDS,
    confidence_view,
    extract,
    load_model,
)
from benchmark.pronunciation_v2.f0_foundation_rmvpe_run import verify_corpus
from benchmark.pronunciation_v2.f0_foundation_run import load_track
from benchmark.pronunciation_v2.f0_foundation_viewer import tracker_path


@pytest.fixture(scope="module")
def corpus():
    return {r["id"]: r for r in verify_corpus(ROOT)}


def test_exact_frozen_corpus_and_all_native_evidence(corpus):
    assert len(corpus) == 49
    assert {p.stem.removesuffix("--rmvpe") for p in (ROOT / "tracks").glob("*.json")} == set(corpus)
    assert {p.stem for p in (ROOT / "activations").glob("*.npz")} == set(corpus)
    for name, row in corpus.items():
        track = load_track(tracker_path(ROOT.parent, name, "rmvpe"))
        evidence = np.load(ROOT / "activations" / f"{name}.npz")
        ts, hz, conf = track.arrays()
        assert track.audio_sha256 == row["sha256"]
        assert evidence["salience"].shape == (len(ts), 360)
        assert np.isfinite(evidence["salience"]).all()
        assert ((evidence["salience"] >= 0) & (evidence["salience"] <= 1)).all()
        np.testing.assert_array_equal(ts, evidence["times"])
        np.testing.assert_allclose(np.diff(ts), 0.01, rtol=0, atol=1e-14)
        np.testing.assert_array_equal(conf, evidence["salience"].max(axis=1))
        np.testing.assert_array_equal(np.nan_to_num(hz), evidence["native_f0_hz"])
        assert np.array_equal(np.isfinite(hz), conf > 0.03)
        assert [f.native_voiced for f in track.frames] == np.isfinite(hz).tolist()


def test_actual_historical_audio_four_context_invariance_and_saved_output(corpus):
    path = corpus["f5dc0cc1"]["audio_path"]
    results = [
        track_record({"audio_path": path, "transcript": text, "tone": i}, "rmvpe").canonical_bytes()
        for i, text in enumerate(("贵州", "鬼粥", "", "arbitrary qzx nonsense"))
    ]
    assert len(set(results)) == 1
    assert results[0] == (ROOT / "tracks/f5dc0cc1--rmvpe.json").read_bytes()


def test_native_full_salience_and_f0_are_deterministic(corpus, tmp_path):
    import torch

    load_model()
    before = torch.get_rng_state().clone()
    path = Path(corpus["syn_steady_70"]["audio_path"])
    a = extract(path, activations_path=tmp_path / "a.npz")
    b = extract(path, activations_path=tmp_path / "b.npz")
    assert a.canonical_bytes() == b.canonical_bytes()
    torch.testing.assert_close(before, torch.get_rng_state())
    for key in np.load(tmp_path / "a.npz").files:
        np.testing.assert_array_equal(
            np.load(tmp_path / "a.npz")[key], np.load(tmp_path / "b.npz")[key]
        )


def test_low_range_and_synthetic_accounting(corpus):
    assert BIN_HZ[0] < 54 < 70 < BIN_HZ[-1]
    saved = json.loads((ROOT / "metrics.json").read_text())
    for name, row in corpus.items():
        if row["kind"] != "synthetic":
            continue
        track = load_track(ROOT / "tracks" / f"{name}--rmvpe.json")
        ts, hz, _ = track.arrays()
        measured = known_f0_metrics(ts, hz, row["truth"])
        expected = next(r for r in saved if r["recording"] == name and r["variant"] == "raw")
        assert all(expected[k] == v for k, v in measured.items())
        assert (
            measured["false_gap_frames"] + measured["compared_frames"]
            == measured["known_voiced_frames"]
        )
        if name == "syn_steady_70":
            assert measured["known_voiced_frames"] == 145
            assert measured["median_error_st"] is None or measured["median_error_st"] >= 0


def test_native_gate_preserves_nulls_and_only_removes_values(corpus):
    for name in corpus:
        track = load_track(ROOT / "tracks" / f"{name}--rmvpe.json")
        before = track.canonical_bytes()
        _, hz, conf = track.arrays()
        gated = confidence_view(track)
        assert track.canonical_bytes() == before
        keep = np.isfinite(gated)
        assert (conf[keep] > 0.05).all()
        np.testing.assert_array_equal(gated[keep], hz[keep])
        assert not np.isfinite(gated[~np.isfinite(hz)]).any()
    with pytest.raises(ValueError):
        confidence_view(track, 0.02)


def test_negative_control_handling_and_sweep_are_honest(corpus):
    metrics = json.loads((ROOT / "metrics.json").read_text())
    sweep = json.loads((ROOT / "threshold-sweep.json").read_text())
    assert len(sweep) == 49 * 5
    assert {r["threshold"] for r in sweep} == set(SWEEP_THRESHOLDS)
    for name, row in corpus.items():
        if row["kind"] != "negative":
            continue
        track = load_track(ROOT / "tracks" / f"{name}--rmvpe.json")
        evidence = np.load(ROOT / "activations" / f"{name}.npz")
        for threshold in SWEEP_THRESHOLDS:
            measured = next(
                r for r in sweep if r["recording"] == name and r["threshold"] == threshold
            )
            assert measured["emitted_frames"] == int((evidence["confidence"] > threshold).sum())
        raw = next(r for r in metrics if r["recording"] == name and r["variant"] == "raw")
        assert raw["emitted_frames"] == sum(f.native_voiced for f in track.frames)
        assert raw["coverage"] == raw["emitted_frames"] / raw["frames"]


def test_saved_alignment_paths_and_previous_native_outputs_unchanged():
    original = Path("/tmp/benma-f0-bakeoff")
    frozen = json.loads((ROOT / "frozen-artifact-hashes.json").read_text())
    for relative, digest in frozen.items():
        assert hashlib.sha256((original / relative).read_bytes()).hexdigest() == digest


def test_viewer_has_all_six_trackers_and_separate_views(corpus):
    page = (ROOT.parent / "viewer.html").read_text()
    assert len(re.findall(r'<details id="', page)) == 49
    for name in corpus:
        assert f'<details id="{name}"' in page
    for label in "ABCDEF":
        assert page.count(f'data-track="{label}"') == 49
        assert page.count(f'class="track-{label}-raw"') == 49
        assert page.count(f'class="track-{label}-minimal"') == 49
        assert page.count(f'class="confidence-{label}"') == 49
    assert "Actual utterance time (seconds)" in page
    assert "max salience &gt;0.05" in page

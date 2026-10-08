"""Final artifact checks only: no model inference or threshold recomputation."""

from __future__ import annotations

import json
import math
import statistics
import struct
from collections import Counter
from html.parser import HTMLParser

import pytest
from silero_vad_audit import MODEL, MODEL_SHA, PRIOR, REPORT, corpus, sha

ENTRIES = json.loads((PRIOR / "corpus.json").read_text())["entries"]
IDS = [entry["id"] for entry in ENTRIES]


def load(name):
    return json.loads((REPORT / name).read_text())


def test_frozen_manifest_and_audio_hashes_are_still_exact():
    manifest, entries, audio = corpus()
    assert (REPORT / "corpus.json").read_bytes() == manifest
    assert len(audio) == len(entries) == 48
    receipt = load("hash-verification.json")
    assert receipt["verified_before_inference"]
    assert receipt["manifest_sha256"] == sha(manifest)
    assert receipt["waveforms"] == {key: sha(data) for key, data in audio.items()}
    assert receipt["counts"] == {"positive": 37, "negative": 10, "unresolved": 1}


@pytest.mark.parametrize("identity", IDS)
def test_every_saved_timeline_preserves_frames_and_provenance(identity):
    timeline = load(f"probabilities/{identity}.json")
    entry = next(e for e in ENTRIES if e["id"] == identity)
    assert timeline["audio_sha256"] == entry["sha256"]
    assert timeline["model_sha256"] == MODEL_SHA
    assert timeline["provenance"] == load("model-provenance.json")
    expected_input_rate = 24000 if identity in ("native_gain", "native_bandlimit") else 16000
    assert timeline["input_sample_rate"] == expected_input_rate
    assert timeline["normalized_sample_rate"] == 16000
    assert timeline["normalized_samples"] == math.ceil(
        timeline["input_samples"] * 16000 / expected_input_rate
    )
    assert timeline["window_samples"] == 512
    assert timeline["context_samples"] == 64
    count = timeline["normalized_samples"]
    assert len(timeline["frames"]) == math.ceil(count / 512)
    for index, frame in enumerate(timeline["frames"]):
        assert frame["start_sample"] == index * 512
        assert frame["end_sample"] == min(count, (index + 1) * 512)
        assert frame["start_seconds"] == frame["start_sample"] / 16000
        assert frame["end_seconds"] == frame["end_sample"] / 16000
        assert frame["window_end_seconds"] == (index + 1) * 512 / 16000
        assert math.isfinite(frame["probability"]) and 0 <= frame["probability"] <= 1


def test_default_and_five_threshold_reports_cover_every_case():
    default = load("default-results.json")
    sweep = load("threshold-results.json")
    assert sweep["default_results_sha256"] == sha((REPORT / "default-results.json").read_bytes())
    assert [r["threshold"] for r in sweep["runs"]] == [0.3, 0.4, 0.5, 0.6, 0.7]
    assert sweep["runs"][2]["rows"] == default["rows"]
    for run in [default, *sweep["runs"]]:
        rows = run["rows"]
        assert [r["id"] for r in rows] == IDS
        assert Counter(r["label"] for r in rows) == {
            "positive": 37,
            "negative": 10,
            "unresolved": 1,
        }
        for row in rows:
            result = row["silero"]
            probabilities = [
                f["probability"] for f in load(f"probabilities/{row['id']}.json")["frames"]
            ]
            assert result["max_probability"] == max(probabilities)
            assert result["median_probability"] == statistics.median(probabilities)
            regions = result["regions_samples"]
            assert result["accepted"] == bool(regions)
            assert result["number_regions"] == len(regions)
            assert result["total_speech_seconds"] == sum(
                (r["end"] - r["start"]) / 16000 for r in regions
            )
            assert result["min_speech_duration_ms"] == 250
        assert run["summary"]["negative_rejected"] == 9
        assert run["summary"]["false_accepts"] == ["silence_accidental"]
        assert run["summary"]["positive_retained"] == sum(
            r["silero"]["accepted"] for r in rows if r["label"] == "positive"
        )
    assert [run["summary"]["positive_retained"] for run in sweep["runs"]] == [34, 33, 33, 32, 31]


def test_model_and_baseline_provenance():
    assert sha(MODEL.read_bytes()) == MODEL_SHA
    provenance = load("model-provenance.json")
    assert provenance["model_size_bytes"] == MODEL.stat().st_size
    assert provenance["providers"] == ["CPUExecutionProvider"]
    baseline = load("baseline-replay.json")
    assert baseline["matches_prior"]
    assert [r["id"] for r in baseline["rows"]] == IDS
    old = {r["id"]: r["current_accepted"] for r in load("default-results.json")["rows"]}
    assert {r["id"]: r["accepted"] for r in baseline["rows"]} == old


class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []
        self.images = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("img", "a"):
            path = attrs.get("src" if tag == "img" else "href")
            assert path
            self.paths.append(path)
            if tag == "img":
                assert attrs.get("alt")
                self.images.append(path)


def test_static_viewer_and_all_required_representatives():
    parser = Resources()
    parser.feed((REPORT / "viewer.html").read_text())
    assert len(parser.images) == 8
    assert {path.split("/")[-1][:-4] for path in parser.images} >= {
        "silence_accidental",
        "silence_periodic",
        "short_human_b",
        "native_gain",
        "7787300e",
        "human_control",
    }
    for path in parser.paths:
        assert (REPORT / path).is_file(), path
    for path in parser.images:
        data = (REPORT / path).read_bytes()
        assert data[:8] == b"\x89PNG\r\n\x1a\n"
        width, height = struct.unpack(">II", data[16:24])
        assert width >= 1200 and height >= 900


def test_runtime_coverage_and_no_gpu():
    timings = load("latency.json")
    assert len(timings["cold"]) == 10
    assert len(timings["measurements"]) == 864
    for backend in ("official", "numpy"):
        subset = [r for r in timings["measurements"] if r["backend"] == backend]
        assert Counter(r["id"] for r in subset) == {key: 9 for key in IDS}
        assert all(r["total_ms"] > 0 and r["real_time_factor"] > 0 for r in subset)
    assert timings["summary"]["official"]["representative_duration_seconds"] == 2.8560625

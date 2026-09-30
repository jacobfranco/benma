"""Forensic invariants against the real frozen corpus and production functions."""

import copy
import json
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter

import acoustic_forensics as af
import pytest
from benma_api.pronunciation.contours import classify_contour, display_contour
from benma_api.schemas import DisplayContour


@pytest.fixture(scope="module")
def selected():
    return af.select_analysis_set(
        af.read_csv(af.EXPERIMENT / "clean-corpus-manifest.csv"),
        af.read_csv(af.EXPERIMENT / "test-results.csv"),
    )


@pytest.fixture(scope="module")
def clip(selected):
    return af.analyze_clip(next(r for r in selected if r["pinyin"] == "ni3"))


def test_selection_complete_deterministic_and_prediction_independent(selected):
    manifest = af.read_csv(af.EXPERIMENT / "clean-corpus-manifest.csv")
    predictions = af.read_csv(af.EXPERIMENT / "test-results.csv")
    changed = [{**p, "prediction": "3" if p["tone"] == "4" else "4"} for p in predictions]
    other = af.select_analysis_set(list(reversed(manifest)), list(reversed(changed)))
    assert [r["source_asset_id"] for r in selected] == [r["source_asset_id"] for r in other]
    assert Counter(r["tone"] for r in selected) == {"3": 13, "4": 21}
    expected = {r["source_asset_id"] for r in predictions if r["tone"] == "3"}
    assert {r["source_asset_id"] for r in selected if r["tone"] == "3"} == expected
    assert sum(r["tone"] == "3" and r["prediction"] == "3" for r in selected) == 2


def test_target_cannot_influence_real_audio_extraction(selected, clip):
    original = next(r for r in selected if r["pinyin"] == "ni3")
    changed = af.analyze_clip(
        {**original, "text": "任意", "pinyin": "irrelevant4", "tone": "4", "prediction": "1"}
    )
    assert changed["identity"] != clip["identity"]
    for key in (
        "acoustics",
        "observed",
        "evidence_region",
        "filtered_measured_frames",
        "full_display_contour",
        "evidence_contour",
        "syllable_display_contour",
    ):
        assert changed[key] == clip[key]


def test_adapter_equals_imported_pipeline_and_ignores_display_geometry(clip):
    raw = clip["acoustics"]["f0"]
    assert clip["full_display_contour"] == display_contour(raw).model_dump()
    assert (
        clip["observed"]
        == classify_contour(DisplayContour(), 0, clip["duration_seconds"], raw=raw).model_dump()
    )
    assert clip["observed"]["classification"] == "4-like"  # Preserve the known failure.


def test_missing_pitch_stays_null_and_gap_duration_is_missing_support(clip):
    raw = clip["acoustics"]["f0"]
    for source, filtered in zip(raw, clip["filtered_measured_frames"], strict=True):
        if source["f0_hz"] is None:
            assert filtered["f0_hz"] is None
            assert filtered["smoothed_semitones"] is None
        assert filtered["f0_hz"] in (None, source["f0_hz"])
    points = [
        {"timestamp_seconds": 0.1 + i * 0.01, "f0_hz": hz}
        for i, hz in enumerate([None, 120, None, None, 110, None])
    ]
    internal = [g for g in af.gap_spans(points) if g["internal"]]
    assert len(internal) == 1
    assert internal[0]["duration"] == 0.02
    assert internal[0]["frames"] == 2


def test_display_bridge_is_separate_and_does_not_fill_measurements(clip):
    # A coherent contour can bridge a short gap for presentation. It must never
    # mutate the source or turn that bridge into measured F0 frames.
    display = {
        "method": "test",
        "segments": [
            [
                {"timestamp_seconds": 0.1, "normalized_semitones": 1},
                {"timestamp_seconds": 0.2, "normalized_semitones": 0.5},
            ],
            [
                {"timestamp_seconds": 0.24, "normalized_semitones": 0},
                {"timestamp_seconds": 0.3, "normalized_semitones": -1},
            ],
        ],
        "minimum_semitones": -4,
        "maximum_semitones": 4,
    }
    observation = {
        "classification": "4-like",
        "confidence": "moderate",
        "reason": "acoustic_shape_only",
        "features": {
            "gap_count": 1,
            "discontinuous_gap_count": 0,
            "contaminated_fraction": 0,
            "tracker_instability_rejected": 0,
            "large_jump_count": 0,
        },
    }
    payload = [{"display_contour": display, "observed_contour": observation, "lexical_tone": 3}]
    before = copy.deepcopy(payload)
    result = subprocess.run(
        ["node", str(af.ROOT / "benchmark/pronunciation_v2/drawer_projection.cjs")],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
    )
    projection = json.loads(result.stdout)[0]
    assert payload == before
    assert projection["interpolation_is_display_only"] is True
    assert len(projection["primary_contour"]["segments"]) == 2
    assert len(projection["normalized_primary_contour"]["segments"]) == 1
    assert len(projection["normalized_primary_contour"]["segments"][0]) == 4
    assert any(p["f0_hz"] is None for p in clip["filtered_measured_frames"])


def test_complete_artifacts_reproduce_saved_frozen_acoustics_and_categories(selected):
    cache = af.Path("/home/jacob/.cache/benma/pronunciation-v2-model/v1-evidence.json")
    saved = {r["source_asset_id"]: r for r in json.loads(cache.read_text())}
    for row in selected:
        artifact = (
            af.OUTPUT / "drawer-payloads" / (row["source_asset_id"].replace(":", "-") + ".json")
        )
        clip = json.loads(artifact.read_text())
        assert clip["acoustics"] == saved[row["source_asset_id"]]["acoustics"]
        assert clip["observed"] == saved[row["source_asset_id"]]["observed"]
        assert clip["research_timing"]["production_alignment_reproduced"] is False
        assert clip["identity"]["tone"] == row["tone"]
        assert clip["drawer_projection"]["interpolation_is_display_only"] is True


def test_production_mobile_and_frozen_experiment_unchanged():
    protected = [
        "services/api",
        "apps/mobile",
        "docs/research/pronunciation-v2/2026-09-29-frozen-wav2vec",
    ]
    subprocess.run(
        ["git", "diff", "--exit-code", "HEAD", "--", *protected],
        cwd=af.ROOT,
        check=True,
        capture_output=True,
    )
    provenance = json.loads((af.OUTPUT / "provenance.json").read_text())
    for path, digest in provenance["protected_file_sha256"].items():
        assert af.sha256(af.ROOT / path) == digest


def test_all_plots_exist_and_parse(selected):
    expected = ["comparison", *[r["source_asset_id"].replace(":", "-") for r in selected]]
    for stem in expected:
        plot = af.OUTPUT / "plots" / f"{stem}.svg"
        assert ET.parse(plot).getroot().tag.endswith("svg")
        assert f"plots/{stem}.svg" in (af.OUTPUT / "index.html").read_text()

"""Focused diagnostics regressions; never load/train a model or touch original takes."""

import copy
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

import numpy as np
from perceptual_tone.common import file_hash, read_json
from perceptual_tone.three_take_report import comparison_markdown, fields
from perceptual_tone.three_take_stability import (
    RUN,
    acoustic_summary,
    compact_grid,
    latency,
    stability,
    verify_snapshot,
    worker_timing,
    write_generated,
)


def test_grid_clamps_both_edges_and_preserves_original():
    grid = compact_grid([1.05, 1.1], [1, 1.1])
    assert all(1 <= v["start"] <= 1.1 and 1 <= v["end"] <= 1.1 for v in grid)
    assert sum(len(v["requested_offsets_ms"]) for v in grid) == 33
    original = next(v for v in grid if [0, 0] in v["requested_offsets_ms"])
    assert (original["start"], original["end"]) == (1.05, 1.1)
    assert len({(v["start"], v["end"]) for v in grid}) == len(grid)


def test_grid_uses_half_open_sample_precision_and_does_not_mutate():
    pool, whole = [0.13, 0.21], [0.1, 0.21]
    before = copy.deepcopy([pool, whole])
    grid = compact_grid(pool, whole)
    assert [pool, whole] == before
    for v in grid:
        assert abs(v["start"] * 16000 - round(v["start"] * 16000)) < 1e-8


def test_short_or_collapsed_variants_are_visible_not_silently_expanded():
    grid = compact_grid([1.07, 1.1], [1, 1.1])
    assert any(v["duration_ms"] <= 0 for v in grid)
    assert any(v["duration_ms"] < 60 for v in grid)


def test_descriptive_states():
    cases = [
        (["T3", "T3"], True, False, "STABLE"),
        (["T3", "T3"], True, True, "MARGIN-SENSITIVE"),
        (["T3", "T2"], True, True, "BOUNDARY-SENSITIVE"),
        (["T3", "T2"], False, False, "UNUSABLE"),
        ([], True, False, "UNUSABLE"),
    ]
    for families, usable, margin, label in cases:
        variants = [{"expanded": {"prediction": p}} for p in families]
        assert stability(variants, "T3", usable=usable, margin_sensitive=margin) == label


def test_f0_support_does_not_bridge_gaps_or_include_right_edge():
    graph = {
        "filtered": {
            "segments": [
                [
                    {"timestamp_seconds": 0.1, "normalized_semitones": 1},
                    {"timestamp_seconds": 0.11, "normalized_semitones": 0},
                ],
                [
                    {"timestamp_seconds": 0.3, "normalized_semitones": 9},
                    {"timestamp_seconds": 0.31, "normalized_semitones": 10},
                ],
            ]
        }
    }
    s = acoustic_summary(graph, [0.1, 0.31])
    assert s["usable_frames"] == 3
    assert np.isclose(s["voiced_support_ms"], 25)
    assert s["islands"] == 2
    assert s["fall_st"] == 1 and s["recovery_st"] == 0


def test_latency_residual_is_not_claimed_as_startup_or_double_counted():
    report = {
        "performance": {
            "alignment_seconds": 12,
            "utterance_total_seconds": 15,
            "learned_seconds": 3.2,
            "encoder_load_this_take_seconds": 3,
        }
    }
    result = latency(report, "Everything took 10.000 seconds\nAlignment round took 1.100 seconds")
    assert result["outside_mfa_internal_seconds"] == 2
    assert np.isclose(result["learned_excluding_encoder_load_seconds"], 0.2)
    assert result["mfa_fraction_of_server_total"] == 0.8
    assert result["corpus_setup_seconds"] is None
    assert result["unmeasured"]
    missing = latency(report, "")
    assert missing["outside_mfa_internal_seconds"] is None


def test_worker_timing_is_logged_bounds():
    log = (
        "2026-10-20 09:08:31,695 - worker - Processing 1-1\n"
        "2026-10-20 09:08:31,700 - worker - Done 1, errors on 0\n"
    )
    assert worker_timing(log)["logged_processing_seconds"] == 0.005


def test_generated_writer_rejects_frozen_and_original_paths():
    for path in (
        RUN / "freeze-manifest.json",
        RUN / "frozen/report.json",
        Path("/tmp/not-a-diagnostic-output/diagnostics.json"),
    ):
        with unittest.TestCase().assertRaisesRegex(ValueError, "not_a_generated"):
            write_generated(path, {})


def read_results():
    if not (RUN / "annotated-diagnostics.json").exists():
        raise unittest.SkipTest("three-take diagnostic artifacts not present")
    return read_json(RUN / "annotated-diagnostics.json")


def test_originals_and_all_preexisting_sources_still_unchanged():
    verified = verify_snapshot()
    assert verified["original_files_verified"] == 279
    assert verified["starting_source_files_verified"] == 1381


def test_every_saved_baseline_reproduced_and_hidden_reuse_is_stable():
    results = read_results()
    count = 0
    for row in results["rows"]:
        assert all(row["clip_pcm_checks"].values())
        hidden = RUN / "hidden-states" / f"{row['take_id']}-{row['index']}.npy"
        assert file_hash(hidden) == row["hidden_sha256"]
        values = np.load(hidden, allow_pickle=False)
        assert values.ndim == 2 and values.shape[1] == 768
        assert np.isfinite(values).all()
        assert all(v["hidden_sha256"] == row["hidden_sha256"] for v in row["variants"])
        if row["expanded"]["status"] == "ok":
            count += 1
            assert max(row["reproduction"].values()) < 1e-6
            original = next(v for v in row["variants"] if [0, 0] in v["requested_offsets_ms"])
            assert original["expanded"]["probabilities"] == row["expanded"]["probabilities"]
    assert count == 10


def test_unusable_units_never_forced_and_variants_respect_original_gates():
    results = read_results()
    for row in results["rows"]:
        for v in row["variants"]:
            assert row["whole"][0] <= v["start"] <= row["whole"][1]
            assert row["whole"][0] <= v["end"] <= row["whole"][1]
            if "expanded" in v:
                assert row["expanded"]["status"] == "ok"
                assert v["duration_ms"] >= 60 - 1e-6
                assert v["pooled_frames"] > 0 and v["f0"]["usable_frames"] > 0
                assert np.isclose(sum(v["expanded"]["probabilities"].values()), 1)
            else:
                assert v["reason"]


def test_report_has_all_fifteen_units_full_probabilities_and_required_measurements():
    results = read_results()
    before = json.dumps(results, sort_keys=True)
    text = comparison_markdown(results["rows"])
    for char in "我想买这个":
        assert f"## {char}" in text
    for label in (
        "Whole read-unit",
        "Tone-bearing",
        "Phones",
        "Owned phone",
        "HuBERT",
        "Voiced support",
        "Usable F0",
        "Expanded full probabilities",
        "Pilot",
        "Deterministic",
        "evidence state",
        "Alignment log likelihood",
    ):
        assert label in text
    assert len(results["rows"]) == 15
    assert all(fields(row) for row in results["rows"])
    assert json.dumps(results, sort_keys=True) == before


def test_orphan_pitch_is_not_reassigned_to_a_syllable():
    results = read_results()
    gaps = results["unowned_gap_evidence"]["d05e1d81a39b4889aa9e461fc32e6c2a"]
    gap = next(g for g in gaps if g["after"] == "想")
    assert gap["region"] == [1.58, 1.94]
    assert gap["acoustics"]["usable_frames"] == 21
    xiang = next(u for u in results["rows"] if u["take"] == 2 and u["character"] == "想")
    assert xiang["whole"] == [1.44, 1.58]
    assert xiang["expanded"]["prediction"] is None


def test_generated_html_contains_all_frozen_playback_and_plot_assets():
    class Assets(HTMLParser):
        def __init__(self):
            super().__init__()
            self.sources = []
            self.audio_count = 0

        def handle_starttag(self, tag, attrs):
            if tag == "audio":
                self.audio_count += 1
            for name, value in attrs:
                if name == "src":
                    self.sources.append(value)

    parser = Assets()
    parser.feed((RUN / "index.html").read_text())
    assert parser.audio_count == 48
    assert len(parser.sources) == 52
    for name in parser.sources:
        path = (RUN / name).resolve()
        assert RUN.resolve() in path.parents
        assert path.is_file()


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(
        unittest.FunctionTestCase(value)
        for name, value in globals().items()
        if name.startswith("test_")
    )

"""Coverage, evidence independence, replay, and prediction-blind artifact contracts."""

import inspect
import json
import re
from collections import Counter
from pathlib import Path

import error_audit as audit
import numpy as np
import pytest


@pytest.fixture(scope="module")
def selected():
    return audit.select_rows(
        audit.af.read_csv(audit.MANIFEST), audit.af.read_csv(audit.PREDICTIONS)
    )


def test_exact_coverage_labels_and_frozen_predictions(selected):
    rows = audit.af.read_csv(audit.OUTPUT / "per-clip.csv")
    assert len(rows) == len(selected) == len({r["source_asset_id"] for r in rows}) == 118
    for source, row in zip(selected, rows, strict=True):
        assert all(source[k] == row[k] for k in audit.IDENTITY)
        for key in (
            "A_prediction",
            "A_confidence",
            "A_correct",
            *[f"A_p_T{i}" for i in range(1, 5)],
        ):
            assert source[key] == row[key]
    assert Counter(r["tone"] for r in rows) == {"1": 30, "2": 29, "3": 29, "4": 30}
    matrix = [
        [
            sum(r["tone"] == str(t) and r["A_prediction"] == str(p) for r in rows)
            for p in range(1, 5)
        ]
        for t in range(1, 5)
    ]
    assert matrix == [[26, 0, 0, 4], [4, 19, 4, 2], [2, 4, 9, 14], [0, 0, 3, 27]]
    t3 = audit.af.read_csv(audit.OUTPUT / "t3-audit.csv")
    assert {r["source_asset_id"] for r in t3} == {
        r["source_asset_id"] for r in rows if r["tone"] == "3"
    }
    assert len(t3) == 29


def test_join_rejects_changed_labels_duplicate_and_missing_id():
    manifest = audit.af.read_csv(audit.MANIFEST)
    predictions = audit.af.read_csv(audit.PREDICTIONS)
    changed = [{**predictions[0], "tone": "4"}, *predictions[1:]]
    with pytest.raises(ValueError, match="identity/label"):
        audit.select_rows(manifest, changed)
    with pytest.raises(ValueError, match=r"coverage|duplicate"):
        audit.select_rows(manifest, [*predictions, predictions[0]])
    with pytest.raises(ValueError, match="coverage"):
        audit.select_rows(manifest[:-1], predictions)


def test_real_audio_extraction_independent_of_targets_and_predictions(selected):
    original = selected[0]
    changed = {
        **original,
        "tone": "4",
        "text": "任意",
        "pinyin": "irrelevant4",
        "A_prediction": "1",
        "A_confidence": ".7",
        "A_correct": "False",
        "A_p_T1": ".7",
        "A_p_T2": ".1",
        "A_p_T3": ".1",
        "A_p_T4": ".1",
    }
    a, b = audit.analyze_row(original), audit.analyze_row(changed)
    diagnostic = audit.extract(audit.ROOT / original["local_path"])
    assert all(a[k] == b[k] == value for k, value in diagnostic.items())
    assert list(inspect.signature(audit.extract).parameters) == ["path"]
    assert a["A_prediction"] != b["A_prediction"]


def test_full_deterministic_replay(tmp_path):
    # Re-extract every real clip twice, not just compare serialized constants.
    first, second = tmp_path / "first", tmp_path / "second"
    audit.run(first)
    audit.run(second)
    expected = sorted(p.relative_to(first) for p in first.rglob("*") if p.is_file())
    assert expected
    for path in expected:
        assert (first / path).read_bytes() == (second / path).read_bytes()
        assert (first / path).read_bytes() == (audit.OUTPUT / path).read_bytes()


def test_waveform_boundaries_preserve_duration_and_handle_no_speech():
    values = np.r_[np.zeros(200), np.full(300, 0.5), np.zeros(105)]
    result, mask, width = audit.boundaries(values, 1000)
    assert width == 10 and sum(mask) == 30
    assert result["leading_low_energy_seconds"] == pytest.approx(0.2)
    assert result["trailing_low_energy_seconds"] == pytest.approx(0.105)
    assert result["active_speech_seconds"] == pytest.approx(0.3)
    assert result["active_speech_rms"] == pytest.approx(0.5)
    assert result["active_speech_fraction"] == pytest.approx(300 / 605)
    quiet, _, _ = audit.boundaries(np.zeros(605), 1000)
    assert quiet["no_active_blocks"] is True
    assert quiet["leading_low_energy_seconds"] is None
    assert quiet["active_speech_rms"] is None


def test_human_audit_unique_complete_blind_and_blank(selected):
    page = (audit.OUTPUT / "human-audit/index.html").read_text()
    raw = re.search(r'<script id="items" type="application/json">(.*?)</script>', page, re.S)[1]
    items = json.loads(raw)
    ids = [r["source_asset_id"] for r in selected]
    assert [r["source_asset_id"] for r in items] == ids
    assert len(items) == len(set(ids)) == 118
    assert all(page.count('"source_asset_id": "' + asset + '"') == 1 for asset in ids)
    assert all(set(r) == {*audit.IDENTITY, "audio_filename"} for r in items)
    assert not re.search(
        r"A_prediction|B_prediction|A_confidence|B_confidence|A_correct|B_correct"
        r"|A_p_T|B_p_T|v1_|acoustic_shape|tracker_instability",
        page,
    )
    assert "connect-src 'none'" in page
    assert not re.search(r"https?://|data:audio|fetch\(|XMLHttpRequest", page)
    template = audit.af.read_csv(audit.OUTPUT / "human-audit/annotations-template.csv")
    assert [r["source_asset_id"] for r in template] == ids
    for source, row in zip(selected, template, strict=True):
        assert all(row[k] == source[k] for k in audit.IDENTITY)
        assert all(row[k] == "" for k in ("realized_tone", "confidence", "note"))
    # Even a contaminated input cannot sneak model fields through the whitelist.
    assert audit.human_items(selected) == items


def test_protected_sources_and_inputs_unchanged_and_no_audio_artifacts():
    provenance = json.loads((audit.OUTPUT / "provenance.json").read_text())
    for kind in ("input_sha256", "source_sha256", "protected_file_sha256"):
        for path, digest in provenance[kind].items():
            assert audit.af.sha256(audit.ROOT / path) == digest
    for path, digest in provenance["generated_artifact_sha256"].items():
        assert audit.af.sha256(audit.OUTPUT / path) == digest
    for row in provenance["audio"]:
        path = audit.ROOT / row["local_path"]
        assert path.is_file() and audit.af.sha256(path) == row["verified_sha256"]
    assert len(provenance["audio"]) == 131
    for path in audit.OUTPUT.rglob("*"):
        if path.is_file():
            assert path.suffix in {".csv", ".json", ".md", ".html", ".svg"}
            assert path.read_bytes()[:4] not in {b"RIFF", b"fLaC", b"OggS"}
    assert not list(audit.OUTPUT.rglob("*.npz"))
    assert not list(audit.OUTPUT.rglob("*.npy"))
    assert Path(audit.__file__).is_relative_to(audit.ROOT / "benchmark/pronunciation_v2")

"""Service-environment tests; no live requests."""

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "research/perceptual-tone-model"
OUT = PACKAGE / "data/generated/azure-timing-replay-v1"
sys.path.insert(0, str(ROOT / "services/api/src"))

from benma_api.pronunciation.azure_alignment import azure_grapheme_units  # noqa: E402


def fixture():
    tid = json.loads((OUT / "freeze-manifest.json").read_text())["take_order"][0]
    return json.loads((OUT / tid / "azure-raw.json").read_text())


def test_raw_serialization_roundtrip_and_existing_mapper_exactness(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "azure_capture", PACKAGE / "scripts/azure_timing_capture.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    value = fixture()
    path = tmp_path / "raw.json"
    module.save(path, value)
    assert json.loads(path.read_text()) == value
    with pytest.raises(FileExistsError):
        module.save(path, {"overwritten": True})
    for tid in json.loads((OUT / "freeze-manifest.json").read_text())["take_order"]:
        raw = json.loads((OUT / tid / "azure-raw.json").read_text())
        saved = json.loads((OUT / tid / "capture.json").read_text())
        assert azure_grapheme_units(
            raw, "我想买这个", duration_seconds=saved["duration_seconds"]
        ) == saved["units"]


def test_word_overlap_and_transcript_mismatch_fail_closed():
    raw = fixture()
    raw["NBest"][0]["Words"][1]["Offset"] = 1
    assert azure_grapheme_units(raw, "我想买这个") == []
    raw = fixture()
    raw["NBest"][0]["Words"][0]["Word"] = "他"
    assert azure_grapheme_units(raw, "我想买这个") == []


def test_grapheme_overlap_rejects_word_without_repair():
    raw = fixture()
    last = raw["NBest"][0]["Words"][-1]
    last["Syllables"][1]["Offset"] = last["Syllables"][0]["Offset"]
    before = copy.deepcopy(raw)
    units = azure_grapheme_units(raw, "我想买这个")
    assert [u["label"] for u in units] == list("我想买")
    assert raw == before


def test_missing_character_timing_stays_missing_and_multichar_word_not_split():
    raw = fixture()
    del raw["NBest"][0]["Words"][-1]["Syllables"][0]["Offset"]
    units = azure_grapheme_units(raw, "我想买这个")
    assert [u["label"] for u in units] == list("我想买个")
    raw = fixture()
    del raw["NBest"][0]["Words"][-1]["Syllables"]
    assert [u["label"] for u in azure_grapheme_units(raw, "我想买这个")] == list("我想买")


def test_missing_single_character_tier_reuses_only_its_exact_word_span():
    raw = fixture()
    del raw["NBest"][0]["Words"][0]["Syllables"]
    units = azure_grapheme_units(raw, "我想买这个")
    assert units[0]["source"] == "azure_character_word"
    assert (units[0]["start_seconds"], units[0]["end_seconds"]) == (0.88, 1.15)


@pytest.mark.parametrize("bad", [None, -1, float("nan"), float("inf"), True])
def test_invalid_grapheme_timestamp_is_not_repaired(bad):
    raw = fixture()
    raw["NBest"][0]["Words"][0]["Syllables"][0]["Offset"] = bad
    assert 0 not in [u["syllable_index"] for u in azure_grapheme_units(raw, "我想买这个")]


def test_readings_scores_and_phone_tones_cannot_change_grapheme_mapping():
    raw = fixture()
    expected = azure_grapheme_units(raw, "我想买这个")
    for word in raw["NBest"][0]["Words"]:
        word["AccuracyScore"] = -1000
        word["Confidence"] = 1
        word["Phonemes"] = [{"Phoneme": "arbitrary 1", "Offset": 0, "Duration": 1}]
        for g in word["Syllables"]:
            g["AccuracyScore"] = 1000
            g["Syllable"] = "tone-marked readings ignored"
    assert azure_grapheme_units(raw, "我想买这个") == expected


def test_outside_audio_fails_closed_and_gap_is_preserved():
    raw = fixture()
    assert azure_grapheme_units(raw, "我想买这个", duration_seconds=1) == []
    units = azure_grapheme_units(raw, "我想买这个")
    assert units[3]["start_seconds"] - units[2]["end_seconds"] == pytest.approx(0.17)

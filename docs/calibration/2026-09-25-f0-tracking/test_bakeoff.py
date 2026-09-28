"""Research-tool invariants only; no synthetic claim about human accuracy."""

import copy
import json

import numpy as np
import parselmouth
import pytest
from bakeoff import CORPUS, DP, OUT, PARAMETERS, analyzer_for, dp_pitch, sequence_path
from benma_api.pronunciation.contours import classify_contour
from benma_api.pronunciation.evidence_region import select_tone_evidence


@pytest.mark.parametrize("name", list(DP))
@pytest.mark.parametrize("shape", ["level", "rise", "valley", "fall"])
def test_supported_shapes_and_no_candidate_hole(name, shape):
    values = {
        "level": np.full(40, 150.0),
        "rise": np.linspace(110, 180, 40),
        "fall": np.linspace(180, 110, 40),
        "valley": np.r_[np.linspace(180, 110, 20), np.linspace(110, 160, 20)],
    }[shape]
    states = [[(0.0, 0.0), (float(hz), 0.9), (float(hz) / 2, 0.65)] for hz in values]
    states[18] = [(0.0, 0.0)]
    chosen = sequence_path(states, [1.0] * 40, DP[name])
    assert [states[i][j][0] for i, j in enumerate(chosen)] == [
        0.0 if i == 18 else hz for i, hz in enumerate(values)
    ]


@pytest.mark.parametrize("name", list(DP))
def test_unvoiced_onset_and_weak_periodicity_stay_missing(name):
    states = [[(0.0, 0.0), (150.0, 0.3)]] * 8 + [[(0.0, 0.0), (150.0, 0.95)]] * 20
    result = sequence_path(states, [1.0] * len(states), DP[name])
    assert result[:8] == [0] * 8
    assert result[8:] == [1] * 20


def test_real_paths_select_only_original_candidates_and_never_mutate_input():
    uid = "3e2ef0b3-c90f-4e9e-ab39-7d4eaca91a74"
    sound = parselmouth.Sound(str(CORPUS / (uid + ".wav")))
    original = sound.to_pitch_ac(**PARAMETERS)
    for name in DP:
        chosen = dp_pitch(sound, name, **PARAMETERS)
        for old, new in zip(original, chosen, strict=True):
            hz = float(new.selected.frequency)
            assert hz in [float(c.frequency) for c in old.candidates]
            if hz:
                assert new.selected.strength >= 0.45
        assert np.array_equal(
            original.selected_array["frequency"],
            sound.to_pitch_ac(**PARAMETERS).selected_array["frequency"],
        )


def test_identity_adapter_and_target_independence_on_human_audio():
    path = CORPUS / "3e2ef0b3-c90f-4e9e-ab39-7d4eaca91a74.wav"
    assert analyzer_for("identity").analyze(path) == analyzer_for("production").analyze(path)
    for method in ["production", *DP, "cc"]:
        raw = analyzer_for(method).analyze(path)["f0"]
        baseline = copy.deepcopy(raw)
        observed = classify_contour(None, 0.47, 1.04, raw=raw).model_dump()
        region = select_tone_evidence(raw, 0.47, 1.04)
        for tone in [1, 2, 3, 4]:
            tagged = [{**p, "expected_tone": tone, "target_pinyin": f"ma{tone}"} for p in raw]
            assert classify_contour(None, 0.47, 1.04, raw=tagged).model_dump() == observed
            assert select_tone_evidence(tagged, 0.47, 1.04) == region
        assert raw == baseline


def test_timing_rejected_not_promoted_and_complete_inventory():
    rows = json.loads((OUT / "comparison.json").read_text())
    assert len(rows) == 67
    spans = [s for r in rows for s in r["spans"]]
    assert len(spans) == 101
    assert sum(s["timing_authorized"] for s in spans) == 95
    for span in spans:
        if not span["timing_authorized"]:
            assert all(
                r["observed"]["classification"] == "unclear" for r in span["methods"].values()
            )
            assert all(r["region"] is None for r in span["methods"].values())

from __future__ import annotations

import copy
import math

import pytest

from benma_api.pronunciation.alignment import parse_textgrid
from benma_api.pronunciation.contours import classify_contour, display_contour, syllable_contour
from benma_api.pronunciation.perceived import perceived_syllables


@pytest.mark.parametrize(
    "text,expected",
    [
        ("聊聊", ["liáo", "liáo"]),
        ("周末", ["zhōu", "mò"]),
        ("你好", ["nǐ", "hǎo"]),
        ("我们", ["wǒ", "men"]),
        ("今天", ["jīn", "tiān"]),
        ("去吧", ["qù", "ba"]),
        ("酒吧", ["jiǔ", "bā"]),
        ("银行", ["yín", "háng"]),
        ("行走", ["xíng", "zǒu"]),
        ("音乐", ["yīn", "yuè"]),
        ("快乐", ["kuài", "lè"]),
        ("长大", ["zhǎng", "dà"]),
        ("长江", ["cháng", "jiāng"]),
        ("重新", ["chóng", "xīn"]),
        ("重量", ["zhòng", "liàng"]),
        ("行", [None]),
        ("重", [None]),
        ("吧", [None]),
    ],
)
def test_contextual_readings(text, expected):
    assert [s.pinyin for s in perceived_syllables(text, {})] == expected


def test_example_preserves_lexical_tones_and_offsets():
    text = "你好，今天我们聊聊周末吧。"  # noqa: RUF001
    syllables = perceived_syllables(text, {"inferred_text": "其他文字"})
    assert [s.lexical_tone for s in syllables] == [3, 3, 1, 1, 3, 0, 2, 2, 1, 4, 0]
    assert all(s.resolution_confidence == "high" for s in syllables)
    assert all(text[s.character_start : s.character_end] == s.characters for s in syllables)
    assert syllables[-1].reading_source == "grammar"
    assert syllables[-1].expected_tone == []


def raw_contour(values):
    return [
        {
            "timestamp_seconds": round(i * 0.01, 4),
            "f0_hz": 180 * 2 ** (v / 12) if v is not None else None,
            "voicing_probability": 0.95 if v is not None else 0,
        }
        for i, v in enumerate(values)
    ]


@pytest.mark.parametrize(
    "values,label",
    [
        ([0.0] * 41, "1-like"),
        ([i * 0.15 for i in range(41)], "2-like"),
        ([-i * 0.15 for i in range(41)], "4-like"),
        ([abs(i - 20) * 0.2 - 4 for i in range(41)], "3-like"),
        ([math.sin(i * 2) * 2 for i in range(41)], "unclear"),
        ([None] * 41, "unclear"),
        ([0] * 5, "unclear"),
        ([i * 0.035 for i in range(41)], "unclear"),
        ([0] * 8 + [None] * 25 + [1] * 8, "unclear"),
    ],
)
def test_acoustic_shape(values, label):
    raw = raw_contour(values)
    display = display_contour(raw)
    observed = classify_contour(display, 0, len(values) * 0.01, raw=raw)
    assert observed.classification == label


@pytest.mark.parametrize("artifact", [12, -12, 25, -30])
def test_isolated_artifact_rejected_without_mutating_raw(artifact):
    raw = raw_contour([0] * 20 + [artifact] + [0] * 20)
    original = copy.deepcopy(raw)
    contour = display_contour(raw)
    assert raw == original
    assert contour.rejected_points == 1
    assert len(contour.segments) == 2
    assert contour.minimum_semitones == -3
    assert contour.maximum_semitones == 3
    assert not any(p.timestamp_seconds == 0.2 for s in contour.segments for p in s)


def test_sustained_high_pitch_preserved_and_no_interpolation():
    raw = raw_contour([0] * 20 + [None] * 12 + [12] * 20)
    contour = display_contour(raw)
    assert contour.rejected_points == 0
    assert len(contour.segments) == 2
    assert sum(len(s) for s in contour.segments) == 40
    assert contour.segments[1][0].timestamp_seconds == 0.32
    assert contour.maximum_semitones - contour.minimum_semitones >= 14
    single = syllable_contour(contour, 0.32, 0.52)
    assert len(single.segments) == 1
    assert (
        classify_contour(single, 0.32, 0.52, raw=raw, timing_reliable=False).classification
        == "unclear"
    )


def test_timestamp_gap_without_explicit_null_breaks_line():
    raw = raw_contour([0] * 20)
    for p in raw[10:]:
        p["timestamp_seconds"] += 0.2
    assert len(display_contour(raw).segments) == 2


def test_textgrid_selects_syllable_or_word_tier_never_combines_phones():
    word = 'item [1]:\nname = "words"\nintervals [1]:\nxmin = 0\nxmax = 0.3\ntext = "周"'
    phone = 'item [2]:\nname = "phones"\nintervals [1]:\nxmin = 0\nxmax = 0.1\ntext = "zh"'
    assert [u["label"] for u in parse_textgrid(word + "\n" + phone)] == ["周"]
    assert parse_textgrid(phone) == []


def test_display_simplification_preserves_gaps_extrema_and_raw():
    from benma_api.pronunciation.contours import simplify_display

    raw = raw_contour([abs(i - 20) * 0.2 - 4 for i in range(41)] + [None] * 12 + [1] * 30)
    contour = display_contour(raw)
    original = contour.model_dump()
    simplified = simplify_display(contour)
    assert contour.model_dump() == original
    assert len(simplified.segments) == 2
    assert sum(len(s) for s in simplified.segments) <= 7
    assert simplified.segments[0][0] == contour.segments[0][0]
    assert simplified.segments[0][-1] == contour.segments[0][-1]
    assert all(p in contour.segments[i] for i, s in enumerate(simplified.segments) for p in s)


@pytest.mark.parametrize("padding", [(6, 12), (9, 24), (8, 15)])
def test_boundary_padding_tolerated_without_mutating_evidence(padding):
    leading, trailing = padding
    raw = raw_contour([None] * leading + [0] * 16 + [None] * trailing)
    before = copy.deepcopy(raw)
    observed = classify_contour(display_contour(raw), 0, len(raw) * 0.01, raw=raw)
    assert observed.classification == "1-like"
    assert observed.voiced_coverage < 0.5
    assert observed.features["active_core_coverage"] == 1
    assert raw == before


@pytest.mark.parametrize(
    "values,reason",
    [
        ([None] * 20 + [0] * 8 + [None] * 20, "insufficient_voicing"),
        ([None] * 60 + [0] * 16 + [None] * 60, "insufficient_voicing"),
        ([0] * 15 + [None] * 15 + [0] * 15, "insufficient_voicing"),
        ([0] * 20 + [8] * 20, "tracker_instability"),
    ],
)
def test_small_locks_fragmentation_and_jumps_still_reject(values, reason):
    raw = raw_contour(values)
    result = classify_contour(display_contour(raw), 0, len(raw) * 0.01, raw=raw)
    assert result.classification == "unclear"
    assert result.reason == reason


def test_contamination_cannot_be_rescued_by_boundary_trimming():
    raw = raw_contour([None] * 8 + [0] * 20 + [None] * 15)
    for point in raw[8:15]:
        point["quality_usable"] = False
    observed = classify_contour(display_contour(raw), 0, 0.43, raw=raw)
    assert observed.reason == "low_frequency_contamination"


@pytest.mark.parametrize(
    "values,label",
    [
        ([0] * 10 + [-0.8] * 10 + [0] * 10 + [2] * 10 + [4] * 10, "2-like"),
        ([1] * 10 + [-1] * 10 + [-3] * 10 + [-1] * 10 + [5] * 10, "3-like"),
        ([4] * 10 + [2] * 10 + [0] * 10 + [-2] * 10 + [-1.5] * 10, "4-like"),
        ([math.sin(i * 2) * 2 for i in range(80)], "unclear"),
        ([i * 0.08 + math.sin(i * 1.3) * 0.3 for i in range(80)], "2-like"),
        ([math.sin(i * 0.14) * 0.4 for i in range(80)], "1-like"),
    ],
)
def test_broad_trajectory_with_onset_sag_rebound_and_jitter(values, label):
    raw = raw_contour(values)
    observed = classify_contour(display_contour(raw), 0, len(raw) * 0.01, raw=raw)
    assert observed.classification == label
    assert "frame_path_length_st" in observed.features
    assert "local_residual_p90_st" in observed.features


@pytest.mark.parametrize("frames", [60, 100, 140])
def test_coherent_rise_not_rejected_for_accumulated_frame_path(frames):
    raw = raw_contour([i * 6 / frames + 0.7 * math.sin(i * 0.5) for i in range(frames)])
    observed = classify_contour(display_contour(raw), 0, frames * 0.01, raw=raw)
    assert observed.classification == "2-like"
    assert observed.features["raw_local_residual_p90_st"] < 1.5


def test_absent_voice_does_not_invent_level_shape_features():
    raw = raw_contour([None] * 40)
    observed = classify_contour(display_contour(raw), 0, 0.4, raw=raw)
    assert observed.classification == "unclear"
    assert "bin_1_st" not in observed.features
    assert "start_st" not in observed.features


@pytest.mark.parametrize("offset,scale", [(0, 1), (4, 1), (-3, 1.1)])
def test_brief_onset_then_sustained_level_is_low_confidence(offset, scale):
    values = [3.5, 2.9, 2.3, 1.5, 0.8] + [0.4 - i * 0.04 for i in range(17)]
    raw = raw_contour([offset + v * scale for v in values])
    before = copy.deepcopy(raw)
    contour = display_contour(raw)
    original = contour.model_dump()
    result = classify_contour(contour, 0, 0.22, raw=raw)
    assert result.classification == "1-like"
    assert result.confidence == "low"
    assert result.reason == "sustained_level_after_onset"
    assert result.features["core_change_st"] > -1
    assert result.features["full_change_st"] < -2
    assert raw == before and contour.model_dump() == original


@pytest.mark.parametrize(
    "values,label",
    [
        ([3 - i * 0.2 for i in range(25)], "4-like"),
        ([6 - i * 0.4 for i in range(25)], "4-like"),
        ([3 - i * 0.3 for i in range(12)] + [-0.6] * 12, "4-like"),
        ([3, 2, 1] + [0] * 15 + [1, 2, 3, 4], "3-like"),
    ],
)
def test_core_does_not_flatten_sustained_falls_or_valleys(values, label):
    raw = raw_contour(values)
    result = classify_contour(display_contour(raw), 0, len(raw) * 0.01, raw=raw)
    assert result.classification == label
    assert result.features["onset_core_candidate"] == 0


@pytest.mark.parametrize(
    "values,label",
    [
        ([1.5, 0.53, 0.23, 0.09, 0.09, 0.1, 0.1, -0.04, -0.26, -0.67, -1.06], "4-like"),
        ([1 - i * 0.22 for i in range(11)], "4-like"),
        ([0] * 11, "unclear"),
        ([i * 0.3 for i in range(11)], "unclear"),
        ([1 - i * 0.3 for i in range(9)], "unclear"),
        ([1, 0.5, 0, None, -0.1, -0.2, -0.4, -0.6, -0.8, -1, -1.2], "unclear"),
        ([0, 1, -1, 2, -2, 1, -1, 2, -2, 0, -3], "unclear"),
    ],
)
def test_short_evidence_requires_coherent_fall(values, label):
    raw = raw_contour([None] * 8 + values + [None] * 19)
    result = classify_contour(display_contour(raw), 0, len(raw) * 0.01, raw=raw)
    assert result.classification == label
    if label == "4-like":
        assert result.reason == "short_coherent_fall"
        assert result.confidence == "low"


@pytest.mark.parametrize("fault", ["weak", "missing", "contaminated", "octave"])
def test_short_fall_cannot_bypass_quality(fault):
    raw = raw_contour([1 - i * 0.25 for i in range(11)])
    for p in raw:
        if fault == "weak":
            p["voicing_probability"] = 0.5
        if fault == "missing":
            p.pop("voicing_probability")
    if fault == "contaminated":
        raw[4]["quality_usable"] = False
    if fault == "octave":
        raw[4]["f0_hz"] *= 2
    assert classify_contour(display_contour(raw), 0, 0.2, raw=raw).classification == "unclear"


@pytest.mark.parametrize(
    "glitches,label", [([], "4-like"), ([20], "4-like"), ([10, 20, 30], "unclear")]
)
def test_filtered_octave_glitches_are_not_a_blanket_quality_exception(glitches, label):
    values = [-i * 0.15 for i in range(41)]
    for i in glitches:
        values[i] += 12
    raw = raw_contour(values)
    original = copy.deepcopy(raw)
    observed = classify_contour(display_contour(raw), 0, 0.41, raw=raw)
    assert observed.classification == label
    assert raw == original
    assert observed.features["large_jump_count"] == 2 * len(glitches)
    if len(glitches) == 1:
        assert observed.confidence == "low"
        assert observed.reason == "isolated_filtered_glitch"
    elif glitches:
        assert observed.reason == "tracker_instability"


def test_disconnected_contradictory_islands_still_reject():
    raw = raw_contour([0] * 12 + [None] * 10 + [12] * 12 + [None] * 10 + [-5] * 12)
    result = classify_contour(display_contour(raw), 0, 0.56, raw=raw)
    assert result.classification == "unclear"


def test_isolated_glitch_does_not_override_contamination():
    raw = raw_contour([-i * 0.15 + (12 if i == 20 else 0) for i in range(41)])
    for p in raw[:10]:
        p["quality_usable"] = False
    result = classify_contour(display_contour(raw), 0, 0.41, raw=raw)
    assert result.classification == "unclear"
    assert result.reason == "low_frequency_contamination"


def test_real_neutral_and_reliable_core_regressions():
    import json
    from pathlib import Path

    from benma_api.pronunciation.contours import simplify_display

    rows = json.loads((Path(__file__).parent / "fixtures/neutral_core_pitch.json").read_text())
    for row in rows:
        raw = row["raw"]
        original = copy.deepcopy(raw)
        display = syllable_contour(display_contour(raw), row["start"], row["end"])
        result = classify_contour(display, row["start"], row["end"], raw=raw)
        assert (result.classification, result.reason) == (row["expected"], row["reason"])
        if row["name"] == "妈":
            core_start = result.features["first_reliable_core_seconds"]
            simplified = simplify_display(display, preserve_seconds=core_start)
            assert any(
                abs(p.timestamp_seconds - core_start) <= 0.000051
                for region in simplified.segments
                for p in region
            )
            assert simplified.segments[0][0] == display.segments[0][0]
            assert (
                result.features["retained_display_frames"] - result.features["reliable_core_frames"]
                == 3
            )
        assert raw == original


def test_mama_uses_lexical_neutral_without_general_reduplication():
    from benma_api.pronunciation.targets import parse_mandarin_target

    target = parse_mandarin_target("妈妈")
    assert target.pinyin_syllables == ["ma1", "ma5"]
    assert target.lexical_tones == [1, 0]
    assert target.surface_tone_expectation["expected_surface_tones"] == [1, 0]
    assert [s.lexical_tone for s in perceived_syllables("妈妈", {})] == [1, 0]
    assert parse_mandarin_target("聊聊").lexical_tones == [2, 2]

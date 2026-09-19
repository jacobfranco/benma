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

    raw = raw_contour([abs(i-20)*.2-4 for i in range(41)] + [None]*12 + [1]*30)
    contour = display_contour(raw)
    original = contour.model_dump()
    simplified = simplify_display(contour)
    assert contour.model_dump() == original
    assert len(simplified.segments) == 2
    assert sum(len(s) for s in simplified.segments) <= 7
    assert simplified.segments[0][0] == contour.segments[0][0]
    assert simplified.segments[0][-1] == contour.segments[0][-1]
    assert all(p in contour.segments[i] for i, s in enumerate(simplified.segments) for p in s)

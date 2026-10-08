"""Exact-text reference semantics, independent of the captured pitch or target."""

import pytest

from benma_api.pronunciation.perceived import perceived_syllables
from benma_api.pronunciation.surface import surface_expectations
from benma_api.pronunciation.targets import parse_mandarin_target


def test_apple_quantity_keeps_citation_and_surface_realization_separate():
    text = "我要一个苹果。"
    syllables = perceived_syllables(text, {"inferred_text": "他要求一个回答"})
    assert [s.characters for s in syllables] == list("我要一个苹果")
    assert [s.lexical_tone for s in syllables] == [3, 4, 1, 4, 2, 3]
    assert [s.expected_surface_tone for s in syllables] == [3, 4, 2, None, 2, 3]
    yao, yi, ge = syllables[1:4]
    assert yao.pinyin == "yào"
    assert yao.reading_source == "grammar"
    assert {"yao1", "yao4"} <= set(yao.alternatives)
    assert yi.surface_rule == "yi_quantity"
    assert ge.pinyin == "gè"
    assert ge.expected_tone  # Citation shape remains available as a reference.
    assert ge.expected_surface_shape == []
    assert ge.surface_rule == "quantity_ge_reduction_optional"
    assert all(s.start_seconds is None and s.observed_gesture == "unclear" for s in syllables)


@pytest.mark.parametrize("text", ["你要两本书", "我们要三杯水", "要一个苹果", "要十二张纸"])
def test_quantity_grammar_generalizes_without_a_sentence_lookup(text):
    yao = next(s for s in perceived_syllables(text, {}) if s.characters == "要")
    assert yao.pinyin == "yào"
    assert yao.lexical_tone == yao.expected_surface_tone == 4
    assert yao.reading_source == "grammar"


@pytest.mark.parametrize("text", ["我要挟他", "我要求他"])
def test_quantity_grammar_does_not_override_lexical_yao1(text):
    yao = next(s for s in perceived_syllables(text, {}) if s.characters == "要")
    assert yao.pinyin == "yāo"
    assert yao.reading_source == "phrase"


@pytest.mark.parametrize("text", ["要", "我要", "要一", "要一，个苹果"])  # noqa: RUF001
def test_quantity_grammar_does_not_use_first_reading_or_cross_punctuation(text):
    yao = next(s for s in perceived_syllables(text, {}) if s.characters == "要")
    assert yao.pinyin is None
    assert yao.reading_source == "unresolved"


@pytest.mark.parametrize("text", ["一个", "一个朋友", "这是一个问题"])
def test_optional_classifier_reduction_does_not_demand_full_t4(text):
    ge = next(s for s in perceived_syllables(text, {}) if s.characters == "个")
    assert ge.lexical_tone == 4
    assert ge.expected_surface_tone is None
    assert ge.surface_rule == "quantity_ge_reduction_optional"


@pytest.mark.parametrize("text", ["个人", "个个", "第一个苹果", "一个个"])
def test_optional_reduction_is_limited_to_existing_quantity_context(text):
    ge = next(s for s in perceived_syllables(text, {}) if s.characters == "个")
    assert ge.expected_surface_tone == 4


def test_explicit_neutral_reading_and_nonadjacent_units_are_preserved():
    assert [e.tone for e in surface_expectations("一个", [0, 1], [1, 0])] == [None, 0]
    assert surface_expectations("一，个", [0, 2], [1, 4])[1].tone == 4  # noqa: RUF001


def test_target_and_perceived_reference_share_optional_reduction():
    target = parse_mandarin_target("我要一个苹果")
    assert target.lexical_tones == [3, 4, 1, 4, 2, 3]
    expectation = target.surface_tone_expectation
    assert expectation["status"] == "context_dependent"
    assert any(
        rule["syllable_index"] == 3
        and rule["expected_surface_tone"] is None
        and rule["type"] == "quantity_ge_reduction_optional"
        for rule in expectation["rules"]
    )

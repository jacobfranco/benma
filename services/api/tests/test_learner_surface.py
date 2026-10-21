"""Downstream grading only: no recording, inference, or corpus work."""

import json
from pathlib import Path

import pytest

from benma_api.pronunciation.learned import comparison
from benma_api.pronunciation.learned_contracts import LearnedRealization
from benma_api.pronunciation.perceived import perceived_syllables
from benma_api.pronunciation.surface import (
    SurfaceExpectation,
    learner_surface_expectations,
    surface_expectations,
)


@pytest.mark.parametrize(
    "lexical,acceptable",
    [
        ([3], [(3,)]),
        ([3, 3], [(2,), (3,)]),
        ([3, 3, 3], [(2, 3), (2,), (3,)]),
        ([3, 4], [(3,), (4,)]),
        ([1, 2, 4], [(1,), (2,), (4,)]),
        ([3, 3, 3, 1], [(2, 3), (2,), (3,), (1,)]),
        ([0, None], [(), ()]),
        ([3, 3, 3, 3], [(), (), (), (3,)]),
    ],
)
def test_generic_lexical_policy(lexical, acceptable):
    # Arbitrary characters prove there are no phrase/character exceptions.
    results = learner_surface_expectations(
        "甲乙丙丁"[: len(lexical)], list(range(len(lexical))), lexical
    )
    assert [s.acceptable_tones for s in results] == acceptable


def test_boundaries_and_neutral_are_distinct_from_unknown():
    results = learner_surface_expectations("甲，乙丙", [0, 2, 3], [3, 3, 3])  # noqa: RUF001
    assert [s.acceptable_tones for s in results] == [(3,), (2,), (3,)]
    neutral, unknown = learner_surface_expectations("甲乙", [0, 1], [0, None])
    assert neutral.resolution == "neutral"
    assert unknown.resolution == "unresolved"
    assert neutral.tone == 0 and unknown.tone is None


def test_physical_reported_families_and_legacy_freeze():
    fixture = json.loads(
        (Path(__file__).parent / "fixtures/learner_grading_physical.json").read_text()
    )
    text = fixture["text"]
    syllables = perceived_syllables(text, {})
    lexical = [s.lexical_tone for s in syllables]
    offsets = [s.character_start for s in syllables]
    results = learner_surface_expectations(text, offsets, lexical)
    assert [list(s.acceptable_tones) for s in results] == [
        u["acceptable_surface_tones"] for u in fixture["units"]
    ]
    assert [s.acceptable_tones for s in results] == [(2, 3), (2,), (3,), (4,), ()]
    assert [s.resolution for s in results] == ["alternatives", "exact", "exact", "exact", "neutral"]
    assert [s.tone for s in surface_expectations(text, offsets, lexical)] == [
        None,
        None,
        None,
        4,
        0,
    ]
    heard = ["T3", "T4", "T3", "T4", None]
    states = [
        comparison(s, LearnedRealization(status="ok" if h else "abstained", prediction=h)).state
        for s, h in zip(results, heard, strict=True)
    ]
    assert states == [
        "experimental_match",
        "experimental_mismatch",
        "experimental_match",
        "experimental_match",
        "neutral",
    ]


@pytest.mark.parametrize("heard", ["T2", "T3"])
@pytest.mark.parametrize("confidence", [0.01, 0.99])
def test_alternative_membership_without_confidence_threshold(heard, confidence):
    expected = SurfaceExpectation(None, "grouping", (2, 3))
    result = comparison(
        expected, LearnedRealization(status="ok", prediction=heard, confidence=confidence)
    )
    assert result.state == "experimental_match"
    assert result.message == f"Correct · Tone {heard[-1]}"


def test_unknown_abstention_and_mismatch_copy():
    r = LearnedRealization(status="ok", prediction="T4")
    assert comparison(2, r).message == "Expected Tone 2 · heard Tone 4"
    assert "can't reliably grade" in comparison(None, r).message
    assert comparison(3, LearnedRealization()).state == "insufficient"
    assert comparison(3, LearnedRealization(status="ok")).state == "insufficient"
    assert (
        comparison(SurfaceExpectation(None, "grouping", (2, 3)), LearnedRealization()).state
        == "insufficient"
    )


@pytest.mark.parametrize(
    "lexical,rules",
    [
        ([3], [None]),
        ([3, 3], ["third_tone_sandhi", None]),
        ([3, 3, 3], ["third_tone_sandhi", "third_tone_sandhi", None]),
        ([1, 2, 4, 0], [None, None, None, None]),
        ([3, 3, 3, 3], [None, None, None, None]),
    ],
)
def test_contextual_metadata_originates_in_generic_resolver(lexical, rules):
    result = learner_surface_expectations(
        "甲乙丙丁"[: len(lexical)], list(range(len(lexical))), lexical
    )
    assert [s.contextual_rule for s in result] == rules
    assert all(s.contextual_rule is None for s in surface_expectations(
        "甲乙丙丁"[: len(lexical)], list(range(len(lexical))), lexical
    ))


def test_contextual_comparison_copy_and_open_rule_contract():
    from benma_api.pronunciation.learned_contracts import LearnedUnit

    expected = learner_surface_expectations("甲乙", [0, 1], [3, 3])[0]
    assert comparison(expected, LearnedRealization(status="ok", prediction="T2")).message == (
        "Correct · Tone 2 here"
    )
    assert comparison(expected, LearnedRealization(status="ok", prediction="T3")).message == (
        "Expected Tone 2 here · heard Tone 3"
    )
    unit = LearnedUnit(
        index=0, characters="甲", target_pinyin="jiǎ", lexical_tone=3,
        expected_surface_tone=2, surface_rule="future_rule", contextual_rule="future_context_rule",
        heard_pinyin=None, realization=LearnedRealization(),
        comparison=comparison(expected, LearnedRealization()),
    )
    assert unit.contextual_rule == "future_context_rule"
    assert unit.target_pinyin == "jiǎ"

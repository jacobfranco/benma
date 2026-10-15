"""Projection-only chunk policy: no acoustics, inference, target or provider work."""

from __future__ import annotations

import copy
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

from benma_api.db.models import PerceivedSpeechAnalysis
from benma_api.pronunciation.chunks import CHUNK_POLICY_VERSION, pronunciation_chunk_candidates
from benma_api.pronunciation.perceived import analysis_response, perceived_syllables
from benma_api.schemas import PerceivedSyllable

ROOT = Path(__file__).resolve().parents[3]
PHYSICAL = Path(__file__).parent / "fixtures/pitch_projection_89cee47e.json"
CASES = ROOT / "apps/mobile/src/__tests__/fixtures/pronunciationChunkCases.json"


@pytest.mark.parametrize(
    "text,words,reasons",
    [
        ("我想买这个", ["这个"], ["demonstrative_classifier"]),
        ("那个", ["那个"], ["demonstrative_classifier"]),
        ("我要一个苹果", ["一个"], ["numeral_classifier"]),
        ("雨伞", ["雨伞"], ["lexical_word"]),
    ],
)
def test_exact_reviewed_candidates(text, words, reasons):
    syllables = perceived_syllables(text, {})
    before = copy.deepcopy(syllables)
    candidates = pronunciation_chunk_candidates(text, syllables)
    assert [c.text for c in candidates] == words
    assert [c.reason for c in candidates] == reasons
    for c in candidates:
        assert text[c.character_start:c.character_end] == c.text
        assert [syllables[i].characters for i in c.syllable_indices] == list(c.text)
    assert syllables == before
    assert pronunciation_chunk_candidates(text, syllables) == candidates


@pytest.mark.parametrize("text", [
    "不是", "今天", "我们", "去吧", "你好吗", "好呢", "好的", "我想", "三个人", "两本书",
    "几个", "多少个", "一本", "第一个", "十一个", "一个个", "一共", "这个个",
    "这，个", "这A个", "这1个", "这🙂个", "贵州",  # noqa: RUF001 — perceived punctuation
])
def test_no_generalization(text):
    assert pronunciation_chunk_candidates(text, perceived_syllables(text, {})) == []


def test_reading_phrase_is_not_a_chunk_or_neutral_attachment_permission():
    for text in ["不是", "今天", "我们", "妈妈"]:
        syllables = perceived_syllables(text, {})
        assert all(s.reading_source == "phrase" for s in syllables)
        assert pronunciation_chunk_candidates(text, syllables) == []


def test_repeated_spans_keep_exact_perceived_offsets_and_indices():
    text = "这个……这个"
    candidates = pronunciation_chunk_candidates(text, perceived_syllables(text, {}))
    assert [(c.character_start, c.character_end, c.syllable_indices) for c in candidates] == [
        (0, 2, [0, 1]), (4, 6, [2, 3]),
    ]


def test_missing_mismatched_and_overridden_readings_fail_closed_without_rewriting():
    for change in [{"pinyin": None}, {"reading_source": "unresolved"}, {"pinyin": "zhèi"}]:
        syllables = perceived_syllables("这个", {})
        syllables[0] = syllables[0].model_copy(update=change)
        before = copy.deepcopy(syllables)
        assert pronunciation_chunk_candidates("这个", syllables) == []
        assert syllables == before
    syllables = perceived_syllables("这个", {})
    assert pronunciation_chunk_candidates("那个", syllables) == []


def test_quantity_uses_saved_surface_context_without_collapsing_lexical_reading():
    syllables = perceived_syllables("一个", {})
    before = copy.deepcopy(syllables)
    assert pronunciation_chunk_candidates("一个", syllables)
    assert (syllables[0].pinyin, syllables[0].lexical_tone, syllables[0].expected_surface_tone) == (
        "yī", 1, 2,
    )
    assert syllables[1].surface_rule == "quantity_ge_reduction_optional"
    assert syllables[1].expected_surface_tone is None
    assert syllables == before
    syllables[0].surface_rule = None  # Old data cannot establish quantity use.
    assert pronunciation_chunk_candidates("一个", syllables) == []


def test_mobile_contract_fixtures_use_the_actual_api_policy_and_readings():
    for case in json.loads(CASES.read_text()):
        syllables = [PerceivedSyllable.model_validate(s) for s in case["syllables"]]
        resolved = perceived_syllables(case["text"], {})
        for actual, saved in zip(resolved, case["syllables"], strict=True):
            assert actual.model_dump(mode="json", include=set(saved)) == saved
        assert [
            c.model_dump() for c in pronunciation_chunk_candidates(case["text"], syllables)
        ] == case["pronunciation_chunk_candidates"]
        assert case["pronunciation_chunk_policy"] == CHUNK_POLICY_VERSION


def test_saved_analysis_serialization_and_history_are_pure_and_target_independent():
    data = json.loads(PHYSICAL.read_text())["data"]
    run = PerceivedSpeechAnalysis(
        id=uuid.uuid4(), perception_run_id=uuid.uuid4(), utterance_id=uuid.uuid4(),
        alignment_reference_text="我想买这个", analyzer_version="saved", status="succeeded",
        error_code=None, latency_ms=0, created_at=datetime.now(UTC), result=data,
    )
    original = copy.deepcopy(run.result)
    response = analysis_response(run)
    assert response.data.pronunciation_chunk_policy == CHUNK_POLICY_VERSION
    assert [c.text for c in response.data.pronunciation_chunk_candidates] == ["这个"]
    for target in [None, "广州", "贵州", "北京"]:
        # Target comparison lives outside the response/planner inputs.
        envelope = {"target": target, "perceived": analysis_response(run).model_dump(mode="json")}
        assert envelope["perceived"] == response.model_dump(mode="json")
    assert analysis_response(run).model_dump_json() == response.model_dump_json()
    assert run.result == original
    for name in ["syllables", "timing_groups", "tone_graph", "measured_pitch"]:
        expected = original.get(name, [])
        actual = response.data.model_dump(mode="json")[name]
        if name != "syllables":
            assert actual == expected
    assert [(s.start_seconds, s.end_seconds) for s in response.data.syllables[-2:]] == [
        (2.34, 2.73), (2.74, 3.04),
    ]

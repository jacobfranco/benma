"""Portable numeric/metadata regressions; never invokes ASR, VAD or a tracker."""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from benchmark.pronunciation_v2.product_acceptance import candidate_acceptance
from benchmark.pronunciation_v2.product_feedback_audit import comparison

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/research/pronunciation-v2/2026-10-09-product-feedback"
CORPUS = (
    ROOT / "docs/research/pronunciation-v2/2026-10-08-gesture-readability/calibration-corpus.json"
)


def test_frozen_source_and_production_replay_are_deterministic():
    context = json.loads((OUT / "expected-context.json").read_text())
    assert hashlib.sha256(CORPUS.read_bytes()).hexdigest() == context["corpus_sha256"]
    command = ["node", str(ROOT / "benchmark/pronunciation_v2/product_feedback.cjs")]
    first = subprocess.check_output(command, input=CORPUS.read_bytes())
    assert first == subprocess.check_output(command, input=CORPUS.read_bytes())
    actual = json.loads(first)
    published = json.loads((OUT / "shape-results.json").read_text())
    assert len(actual) == 53
    # Historical shape diagnostics predate dominant-gesture features. Preserve
    # their family decisions; the current tone-feedback audit checks full current
    # diagnostics against its own production replay, without rewriting history.
    assert [(r["id"], r["result"]["shape"]) for r in actual] == [
        (r["id"], r["shape"]["shape"]) for r in published
    ]
    for current, old in zip(actual, published, strict=True):
        if old["shape"]["shape"] == "UNCLEAR":
            assert current["result"]["reason"] == old["shape"]["reason"]
    assert sum(r["shape"]["shape"] == r["manual_geometry"] != "UNCLEAR" for r in published) == 28
    assert [
        r["id"]
        for r in published
        if r["shape"]["shape"] != "UNCLEAR" and r["manual_geometry"] == "UNCLEAR"
    ] == ["40357072:想"]


def test_exact_nine_approved_requests_and_known_acceptance_blocker():
    manifest = json.loads((OUT / "approved-upload-manifest.json").read_text())
    result = json.loads((OUT / "acceptance-preflight.json").read_text())
    rows = result["requests"]
    assert len(rows) == 9
    assert [(r["id"], r["sha256"]) for r in rows] == [(r["id"], r["sha256"]) for r in manifest]
    for r in rows:
        assert r["request_fields"] == {"model": "gpt-transcribe", "response_format": "json"}
        assert not r["prompt_supplied"] and not r["language_hint_supplied"]
        state, reason = candidate_acceptance(
            no_speech=r["current_presence"]["no_speech"],
            response=r.get("response"),
            request_ok=r.get("http_status") == 200,
        )
        assert (state, reason) == (r["proposed_acceptance"], r["acceptance_reason"])
    by_id = {r["id"]: r for r in rows}
    # This is a documented failure of the proposed gate, not a passing safety claim.
    assert by_id["throat_clear"]["response"]["languages"] == []
    assert by_id["low_f0_excerpt"]["response"]["languages"] == []
    assert by_id["low_f0_excerpt"]["proposed_acceptance"] == "UNKNOWN"
    assert by_id["short_human_c"]["request_error"] == "ReadTimeout"
    assert result["prior_english_probe"]["response"]["languages"] == [{"code": "en"}]


@pytest.mark.parametrize("text", ["", "错误的普通话", "八伞五木", "arbitrary text"])
def test_proposal_does_not_require_transcript_lexical_correctness(text):
    assert (
        candidate_acceptance(
            no_speech=False, response={"text": text, "languages": [{"code": "zh"}]}
        )[0]
        == "ACCEPT"
    )


def test_ambiguous_language_is_not_silence_or_a_ranked_language_vote():
    assert candidate_acceptance(no_speech=False, response={"languages": []}) == (
        "UNKNOWN",
        "no_reliable_language",
    )
    for codes in [["zh", "en"], ["en", "zh"]]:
        assert candidate_acceptance(
            no_speech=False, response={"languages": [{"code": s} for s in codes]}
        ) == ("UNKNOWN", "multiple_detected_languages")
    assert (
        candidate_acceptance(no_speech=True, response={"languages": [{"code": "zh"}]})[0] == "RETRY"
    )


@pytest.mark.parametrize(
    ("shape", "expected", "state"),
    [
        ({"shape": "RISING", "features": {"net_st": 3}}, "RISING", "STRONG_MATCH"),
        ({"shape": "RISING", "features": {"net_st": 1.6}}, "RISING", "PARTIAL_OR_WEAK"),
        ({"shape": "RISING", "features": {"net_st": 3}}, "FALLING", "CLEAR_DIFFERENCE"),
        ({"shape": "UNCLEAR", "features": {}}, "FALLING", "UNAVAILABLE"),
        ({"shape": "DIP_RISE", "features": {"recovery_st": 1.2}}, "LOW_OR_DIP", "PARTIAL_OR_WEAK"),
        ({"shape": "LEVEL", "features": {}}, "FLEXIBLE_NEUTRAL", "UNAVAILABLE"),
        ({"shape": "DIP_RISE", "features": {}}, "CONTEXT_UNRESOLVED", "UNAVAILABLE"),
    ],
)
def test_research_comparison_semantics(shape, expected, state):
    assert comparison(shape, expected, False)[0] == state
    assert comparison(shape, expected, True)[0] == "UNAVAILABLE"

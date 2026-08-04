from __future__ import annotations

from benchmark.evaluation.fusion import ToneEvidence, decide_tone, evaluate_policy


def test_provider_f0_policy_exposes_conflict_instead_of_overriding() -> None:
    evidence = ToneEvidence(
        sample_id="s1",
        human_error=False,
        expected_tone=2,
        provider_tones=(4,),
        f0_direction="rising",
    )
    assert decide_tone(evidence, policy="provider_only")[0] == "flag"
    decision, reason = decide_tone(evidence, policy="provider_f0_non_conflict")
    assert decision == "abstain"
    assert "conflict" in reason


def test_two_provider_policy_requires_agreement_and_reports_far_frr() -> None:
    observations = [
        ToneEvidence("error", True, 2, (4, 4)),
        ToneEvidence("acceptable", False, 2, (2, 2)),
        ToneEvidence("conflict", True, 2, (4, 3)),
    ]
    report = evaluate_policy(observations, policy="two_provider_agreement")
    assert report["promotion_state"] == "exploratory_only"
    assert report["false_acceptance"]["denominator"] == 1
    assert report["false_acceptance"]["numerator"] == 0
    assert report["false_rejection"]["denominator"] == 1
    assert report["error_abstentions"] == 1

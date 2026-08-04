"""Transparent candidate evidence policies; no learned classifier and no auto-promotion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from benchmark.evaluation.calibration import rate_estimate

Decision = Literal["flag", "accept", "abstain"]
Policy = Literal[
    "provider_only",
    "provider_f0_non_conflict",
    "two_provider_agreement",
    "provider_score_threshold",
]


@dataclass(frozen=True, slots=True)
class ToneEvidence:
    sample_id: str
    human_error: bool
    expected_tone: int | None
    provider_tones: tuple[int | None, ...]
    f0_direction: Literal["level", "rising", "falling"] | None = None
    recording_quality_usable: bool = True
    provider_score: float | None = None


def decide_tone(
    evidence: ToneEvidence,
    *,
    policy: Policy,
    score_threshold: float | None = None,
) -> tuple[Decision, str]:
    if not evidence.recording_quality_usable or evidence.expected_tone is None:
        return "abstain", "unusable recording or expected tone unavailable"
    if policy == "provider_score_threshold":
        if evidence.provider_score is None or score_threshold is None:
            return "abstain", "score or threshold unavailable"
        return (
            ("flag", "provider score below threshold")
            if evidence.provider_score < score_threshold
            else ("accept", "provider score at or above threshold")
        )
    available = [tone for tone in evidence.provider_tones if tone is not None]
    if not available:
        return "abstain", "provider tone unavailable"
    if policy == "two_provider_agreement":
        if len(available) < 2 or len(set(available[:2])) != 1:
            return "abstain", "two provider hypotheses unavailable or conflicting"
        return (
            ("flag", "two providers agree on a non-expected tone")
            if available[0] != evidence.expected_tone
            else ("accept", "two providers agree on expected tone")
        )
    detected = available[0]
    if detected == evidence.expected_tone:
        return "accept", "provider detected expected tone"
    if policy == "provider_only":
        return "flag", "valid provider hypothesis differs from expected tone"
    directions = {1: "level", 2: "rising", 4: "falling"}
    expected_direction = directions.get(evidence.expected_tone)
    detected_direction = directions.get(detected)
    if evidence.f0_direction is None or expected_direction is None or detected_direction is None:
        return "flag", "provider mismatch; F0 cannot adjudicate"
    if evidence.f0_direction == expected_direction:
        return "abstain", "provider and F0 conflict"
    return "flag", "provider mismatch is not contradicted by simple F0 direction"


def evaluate_policy(
    evidence: list[ToneEvidence],
    *,
    policy: Policy,
    score_threshold: float | None = None,
) -> dict[str, object]:
    decisions = [
        (item, *decide_tone(item, policy=policy, score_threshold=score_threshold))
        for item in evidence
    ]
    errors = [(item, decision) for item, decision, _ in decisions if item.human_error]
    acceptable = [(item, decision) for item, decision, _ in decisions if not item.human_error]
    error_decisions = [decision for _, decision in errors if decision != "abstain"]
    acceptable_decisions = [
        decision for _, decision in acceptable if decision != "abstain"
    ]
    return {
        "policy": policy,
        "promotion_state": "exploratory_only",
        "false_acceptance": rate_estimate(
            error_decisions.count("accept"), len(error_decisions)
        ).normalized(),
        "false_rejection": rate_estimate(
            acceptable_decisions.count("flag"), len(acceptable_decisions)
        ).normalized(),
        "error_abstentions": sum(decision == "abstain" for _, decision in errors),
        "acceptable_abstentions": sum(
            decision == "abstain" for _, decision in acceptable
        ),
        "decisions": [
            {
                "sample_id": item.sample_id,
                "human_error": item.human_error,
                "decision": decision,
                "reason": reason,
            }
            for item, decision, reason in decisions
        ],
    }

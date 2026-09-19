"""Central capability maturity and provider-candidate status."""

from __future__ import annotations

from typing import Any

from benma_api.config import Settings
from benma_api.speech.provider_lifecycle import provider_status_manifest

WORDING_POLICY = {
    "raw_evidence": "factual_provider_or_acoustic_observation_only",
    "experimental": "detected_appears_likely_with_conflict_and_missingness",
    "calibrated": "stronger_diagnostic_only_with_matching_calibration_scope",
}


def pronunciation_provider_statuses() -> list[dict[str, Any]]:
    return provider_status_manifest()


def pronunciation_capability_policy(settings: Settings) -> dict[str, Any]:
    return {
        "tone_interpretation": (
            "experimental" if settings.enable_experimental_tone_interpretation else "raw_evidence"
        ),
        "categorical_tone_judgment": "unavailable",
        "reference_contour_role": "visual_example_not_grading_truth",
        "intelligibility_inference": "unavailable",
        "wording_policy": WORDING_POLICY,
        "provider_candidates": pronunciation_provider_statuses(),
    }

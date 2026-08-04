"""Visibly synthetic development providers."""

from __future__ import annotations

from benma_api.speech.contracts import (
    AssessmentEvidence,
    AssessmentProviderResponse,
    KnownTargetAssessmentInput,
    PerceptionEvidence,
    PerceptionProviderResponse,
    UnknownTargetPerceptionInput,
)


class ReplayPerceptionProvider:
    provider_name = "replay"
    product_name = "mandarin-perception-fixture-v1"
    adapter_version = "1.0.0"

    def perceive(self, request: UnknownTargetPerceptionInput) -> PerceptionProviderResponse:
        transcript = "我明天想去背景。"
        raw = {
            "text": transcript,
            "fixture": "unknown-target-mandarin-v1",
            "synthetic": True,
            "audio_size_received": len(request.canonical_audio),
        }
        return PerceptionProviderResponse(
            evidence=PerceptionEvidence(
                transcript=transcript,
                alternatives=None,
                tokens=None,
                segments=None,
                provider_uncertainty=None,
                detected_language="zh",
                evidence_status="synthetic_replay",
            ),
            raw_payload=raw,
            provider_version="fixture-v1",
        )


class ReplayPronunciationProvider:
    provider_name = "replay"
    product_name = "mandarin-pronunciation-fixture-v1"
    adapter_version = "1.0.0"

    def assess(self, request: KnownTargetAssessmentInput) -> AssessmentProviderResponse:
        text = str(request.target_snapshot["text"])
        raw = {
            "target": text,
            "PronScore": 81,
            "synthetic": True,
            "fixture": "known-target-mandarin-v1",
        }
        return AssessmentProviderResponse(
            evidence=AssessmentEvidence(
                overall_score=81,
                pronunciation_score=79,
                syllables=[],
                unsupported_capabilities=[
                    "detected lexical tone",
                    "tone score",
                    "phone-level evidence",
                ],
                evidence_status="synthetic_replay",
            ),
            raw_payload=raw,
            provider_version="fixture-v1",
        )

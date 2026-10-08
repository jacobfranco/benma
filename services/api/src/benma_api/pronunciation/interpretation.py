"""Derived pronunciation observations with calibration-gated language."""

from __future__ import annotations

import json
import uuid
from enum import StrEnum
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from benma_api.config import Settings
from benma_api.db.models import (
    AcousticRun,
    AlignmentRun,
    AssessmentRun,
    PronunciationAttempt,
    PronunciationInterpretationRun,
    PronunciationTarget,
)
from benma_api.errors import AuthorizationError


class CapabilityState(StrEnum):
    UNAVAILABLE = "unavailable"
    RAW_EVIDENCE = "raw_evidence"
    EXPERIMENTAL = "experimental"
    CALIBRATED = "calibrated"


INTERPRETER_VERSION = "pronunciation-observations-v1.3-descriptive-provider-labels"


def has_live_assessment(assessment: AssessmentRun | None) -> bool:
    """Completion alone is not evidence: replay/unknown provenance fails closed."""
    return bool(
        assessment
        and assessment.status == "succeeded"
        and assessment.provider != "replay"
        and (assessment.normalized_result or {}).get("evidence_status") == "live_provider"
    )


def interpreter_configuration(settings: Settings) -> dict[str, bool]:
    return {
        "enable_experimental_tone_interpretation": (
            settings.enable_experimental_tone_interpretation
        ),
        "enable_categorical_tone_judgment": settings.enable_categorical_tone_judgment,
    }


def diff_observations(
    baseline: list[dict[str, Any]], replayed: list[dict[str, Any]]
) -> dict[str, Any]:
    """Produce a stable, reviewable diff without changing stored evidence."""

    def key(item: dict[str, Any]) -> str:
        return json.dumps(
            [item.get("category"), item.get("syllable_index"), item.get("kind")],
            ensure_ascii=False,
            separators=(",", ":"),
        )

    before = {key(item): item for item in baseline}
    after = {key(item): item for item in replayed}
    added = [after[item] for item in sorted(after.keys() - before.keys())]
    removed = [before[item] for item in sorted(before.keys() - after.keys())]
    changed = [
        {"key": item, "before": before[item], "after": after[item]}
        for item in sorted(before.keys() & after.keys())
        if before[item] != after[item]
    ]
    return {
        "changed": bool(added or removed or changed),
        "added": added,
        "removed": removed,
        "modified": changed,
    }


def _tone(value: Any) -> int | None:
    if isinstance(value, int) and value in {0, 1, 2, 3, 4, 5}:
        return 0 if value == 5 else value
    if isinstance(value, str):
        digits = [character for character in value if character in "012345"]
        if digits:
            parsed = int(digits[-1])
            return 0 if parsed == 5 else parsed
    return None


def _acoustic_direction(points: list[dict[str, Any]]) -> tuple[str | None, float | None]:
    values = [
        float(point["normalized_semitones"])
        for point in points
        if point.get("normalized_semitones") is not None
    ]
    if len(values) < 2:
        return None, None
    change = values[-1] - values[0]
    if change > 0:
        return "rising", round(change, 3)
    if change < 0:
        return "falling", round(change, 3)
    return "level", 0.0


def _syllable_points(
    acoustic: dict[str, Any] | None,
    alignment: dict[str, Any] | None,
    index: int,
    syllable_count: int,
) -> list[dict[str, Any]]:
    if acoustic is None:
        return []
    points = acoustic.get("f0")
    if not isinstance(points, list):
        return []
    if syllable_count == 1:
        return [item for item in points if isinstance(item, dict)]
    if not alignment:
        return []
    quality = alignment.get("quality")
    units = alignment.get("units")
    if (
        not isinstance(quality, dict)
        or not quality.get("usable_for_syllable_visualization")
        or not isinstance(units, list)
        or index >= len(units)
    ):
        return []
    unit = units[index]
    if not isinstance(unit, dict):
        return []
    start = float(unit.get("start_seconds", -1))
    end = float(unit.get("end_seconds", -1))
    return [
        item
        for item in points
        if isinstance(item, dict) and start <= float(item.get("timestamp_seconds", -1)) <= end
    ]


def interpret_evidence(
    *,
    target: PronunciationTarget,
    assessment: AssessmentRun | None,
    acoustic: AcousticRun | None,
    alignment: AlignmentRun | None,
    settings: Settings,
) -> tuple[list[dict[str, Any]], CapabilityState]:
    observations: list[dict[str, Any]] = []
    acoustic_result = (
        acoustic.normalized_result if acoustic and acoustic.status == "succeeded" else None
    )
    recording_quality = acoustic_result.get("recording_quality") if acoustic_result else None
    if isinstance(recording_quality, dict) and recording_quality.get("status") != "usable":
        observations.append(
            {
                "category": "AUDIO_QUALITY",
                "syllable_index": None,
                "kind": "invalid_audio",
                "message": "This recording could not be evaluated reliably.",
                "details": recording_quality,
                "capability_state": CapabilityState.RAW_EVIDENCE,
            }
        )
        return observations, CapabilityState.RAW_EVIDENCE

    assessment_result = (
        assessment.normalized_result if assessment and has_live_assessment(assessment) else None
    )
    provider_syllables = (
        assessment_result.get("syllables", []) if isinstance(assessment_result, dict) else []
    )
    if not isinstance(provider_syllables, list):
        provider_syllables = []
    expectation = target.surface_tone_expectation or {}
    expected = expectation.get("expected_surface_tones")
    expected_tones = expected if isinstance(expected, list) else target.lexical_tones
    alignment_result = (
        alignment.normalized_result if alignment and alignment.status == "succeeded" else None
    )
    experimental = settings.enable_experimental_tone_interpretation

    for index, lexical in enumerate(target.lexical_tones):
        expected_tone = (
            _tone(expected_tones[index]) if index < len(expected_tones) else _tone(lexical)
        )
        provider = provider_syllables[index] if index < len(provider_syllables) else {}
        provider_tone = _tone(provider.get("detected_tone")) if isinstance(provider, dict) else None
        points = _syllable_points(
            acoustic_result,
            alignment_result,
            index,
            len(target.lexical_tones),
        )
        direction, change = _acoustic_direction(points)
        base = {
            "category": "TONE",
            "syllable_index": index,
            "lexical_tone": _tone(lexical),
            "expected_surface_tone": expected_tone,
            "observed_provider_tone": provider_tone,
            "f0_direction": direction,
            "f0_change_semitones": change,
        }
        if expected_tone == 0:
            observations.append(
                {
                    **base,
                    "kind": "neutral_context_observation",
                    "agreement": "not_calibrated",
                    "message": (
                        "Neutral tone has context-dependent pitch. "
                        + (f"Measured pitch moved {direction}. " if direction else "")
                        + "Observed shape is not a correctness judgment."
                    ),
                    "capability_state": CapabilityState.RAW_EVIDENCE,
                }
            )
        elif provider_tone is not None and provider_tone != expected_tone and experimental:
            contour_directions = {1: "level", 2: "rising", 4: "falling"}
            expected_direction = (
                contour_directions.get(expected_tone) if expected_tone is not None else None
            )
            provider_direction = contour_directions.get(provider_tone)
            agreement = (
                "conflicted"
                if expected_direction is not None and direction == expected_direction
                else "agreement"
                if provider_direction is not None and direction == provider_direction
                else "inconclusive"
                if direction is not None
                else "provider_only"
            )
            message = (
                f"Experimental provider tone label: T{provider_tone}; "
                f"the reference surface tone is T{expected_tone}. "
                "This is not a pronunciation grade."
            )
            if agreement == "agreement":
                message += f" The measured pitch was {direction}."
            elif agreement == "conflicted":
                message += (
                    " The measured pitch points in a different direction, "
                    "so the evidence conflicts."
                )
            elif agreement == "inconclusive":
                message += (
                    f" The measured pitch was {direction}; this simple contour rule "
                    "cannot reconcile the signals."
                )
            observations.append(
                {
                    **base,
                    "kind": "tone_evidence_mismatch" if agreement != "conflicted" else "conflict",
                    "agreement": agreement,
                    "message": message,
                    "capability_state": CapabilityState.EXPERIMENTAL,
                }
            )
        elif provider_tone is not None:
            observations.append(
                {
                    **base,
                    "kind": "provider_tone_observation",
                    "agreement": "provider_only" if direction is None else "not_calibrated",
                    "message": (
                        f"Uncalibrated provider tone label: T{provider_tone}. "
                        "This is not a pronunciation grade."
                    ),
                    "capability_state": CapabilityState.RAW_EVIDENCE,
                }
            )
        elif direction is not None:
            observations.append(
                {
                    **base,
                    "kind": "acoustic_observation",
                    "agreement": "acoustic_only",
                    "message": f"Measured pitch moved {direction} through this syllable.",
                    "capability_state": CapabilityState.RAW_EVIDENCE,
                }
            )
        else:
            observations.append(
                {
                    **base,
                    "kind": "tone_unavailable",
                    "agreement": "unavailable",
                    "message": "Pitch interpretation is unavailable for this syllable.",
                    "capability_state": CapabilityState.UNAVAILABLE,
                }
            )
    overall = (
        CapabilityState.EXPERIMENTAL
        if any(item["capability_state"] == CapabilityState.EXPERIMENTAL for item in observations)
        else CapabilityState.RAW_EVIDENCE
        if any(item["capability_state"] == CapabilityState.RAW_EVIDENCE for item in observations)
        else CapabilityState.UNAVAILABLE
    )
    return observations, overall


class PronunciationInterpretationService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    def run(
        self,
        *,
        account_id: uuid.UUID,
        attempt_id: uuid.UUID,
        assessment: AssessmentRun | None,
        acoustic: AcousticRun | None,
        alignment: AlignmentRun | None,
        reuse: bool = True,
    ) -> PronunciationInterpretationRun:
        attempt = self.db.get(PronunciationAttempt, attempt_id)
        if attempt is None or attempt.account_id != account_id:
            raise AuthorizationError("pronunciation attempt was not found")
        target = self.db.get(PronunciationTarget, attempt.target_id)
        if target is None or target.account_id != account_id:
            raise AuthorizationError("pronunciation target was not found")
        evidence_ids = {
            "assessment_run_id": str(assessment.id) if assessment else None,
            "acoustic_run_id": str(acoustic.id) if acoustic else None,
            "alignment_run_id": str(alignment.id) if alignment else None,
        }
        configuration = interpreter_configuration(self.settings)
        if reuse:
            candidates = self.db.scalars(
                select(PronunciationInterpretationRun)
                .where(
                    PronunciationInterpretationRun.account_id == account_id,
                    PronunciationInterpretationRun.pronunciation_attempt_id == attempt_id,
                    PronunciationInterpretationRun.interpreter_version == INTERPRETER_VERSION,
                )
                .order_by(PronunciationInterpretationRun.created_at.desc())
            )
            for candidate in candidates:
                if (
                    candidate.input_evidence_run_ids == evidence_ids
                    and candidate.interpreter_configuration == configuration
                ):
                    return candidate
        observations, capability = interpret_evidence(
            target=target,
            assessment=assessment,
            acoustic=acoustic,
            alignment=alignment,
            settings=self.settings,
        )
        run = PronunciationInterpretationRun(
            account_id=account_id,
            pronunciation_attempt_id=attempt_id,
            interpreter_version=INTERPRETER_VERSION,
            interpreter_configuration=configuration,
            input_evidence_run_ids=evidence_ids,
            structured_observations=observations,
            capability_state=capability,
        )
        self.db.add(run)
        self.db.commit()
        return run

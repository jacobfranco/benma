"""Pronunciation-laboratory orchestration over immutable evidence runs."""

from __future__ import annotations

import uuid
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
    ReferenceSpeechAsset,
)
from benma_api.errors import AuthorizationError, BenmaError
from benma_api.pronunciation.acoustics import (
    AcousticAnalysisService,
    AutocorrelationAcousticAnalyzer,
    DisabledAcousticAnalyzer,
)
from benma_api.pronunciation.alignment import AlignmentService, build_aligner
from benma_api.pronunciation.capabilities import pronunciation_provider_statuses
from benma_api.pronunciation.interpretation import PronunciationInterpretationService
from benma_api.pronunciation.reference import ReferenceSpeechService
from benma_api.pronunciation.service import AssessmentService
from benma_api.schemas import (
    AcousticRunResponse,
    AlignmentRunResponse,
    AssessmentRunResponse,
    InterpretationRunResponse,
    PronunciationAttemptResponse,
    PronunciationResultResponse,
    PronunciationSyllableResult,
    PronunciationTargetResponse,
    ReferenceSpeechResponse,
)
from benma_api.speech.providers.factory import build_assessment_provider
from benma_api.storage.audio_store import AudioObjectStore


def _latest[RunT](db: Session, model: type[RunT], *criteria: Any) -> RunT | None:
    return db.scalar(
        select(model).where(*criteria).order_by(model.created_at.desc())  # type: ignore[attr-defined]
    )


def reference_response(asset: ReferenceSpeechAsset) -> ReferenceSpeechResponse:
    return ReferenceSpeechResponse(
        id=asset.id,
        target_id=asset.target_id,
        provider=asset.provider,
        voice=asset.voice,
        locale=asset.locale,
        model_version=asset.model_version,
        generation_config=asset.generation_config,
        target_snapshot=asset.target_snapshot,
        status=asset.status,
        error_code=asset.error_code,
        error_message=asset.error_message,
        audio_url=(
            f"/v1/reference-speech/{asset.id}/audio"
            if asset.status == "succeeded" and asset.audio_asset_id
            else None
        ),
        acoustic_result=asset.acoustic_result,
        created_at=asset.created_at,
    )


def acoustic_response(run: AcousticRun) -> AcousticRunResponse:
    return AcousticRunResponse(
        id=run.id,
        utterance_id=run.utterance_id,
        algorithm=run.algorithm,
        algorithm_version=run.algorithm_version,
        parameters=run.parameters,
        normalized_result=run.normalized_result,
        latency_ms=run.latency_ms,
        status=run.status,
        error_code=run.error_code,
        error_message=run.error_message,
        created_at=run.created_at,
    )


def alignment_response(run: AlignmentRun) -> AlignmentRunResponse:
    return AlignmentRunResponse(
        id=run.id,
        pronunciation_attempt_id=run.pronunciation_attempt_id,
        algorithm=run.algorithm,
        algorithm_version=run.algorithm_version,
        normalized_result=run.normalized_result,
        quality=run.quality,
        latency_ms=run.latency_ms,
        status=run.status,
        error_code=run.error_code,
        error_message=run.error_message,
        created_at=run.created_at,
    )


def interpretation_response(
    run: PronunciationInterpretationRun,
) -> InterpretationRunResponse:
    return InterpretationRunResponse(
        id=run.id,
        pronunciation_attempt_id=run.pronunciation_attempt_id,
        interpreter_version=run.interpreter_version,
        interpreter_configuration=run.interpreter_configuration,
        input_evidence_run_ids=run.input_evidence_run_ids,
        structured_observations=run.structured_observations,
        capability_state=run.capability_state,
        created_at=run.created_at,
    )


def assessment_response(run: AssessmentRun) -> AssessmentRunResponse:
    return AssessmentRunResponse(
        id=run.id,
        pronunciation_attempt_id=run.pronunciation_attempt_id,
        provider=run.provider,
        product=run.product,
        provider_version=run.provider_version,
        adapter_version=run.adapter_version,
        target_snapshot=run.target_snapshot,
        git_commit_sha=run.git_commit_sha,
        audio_sha256=run.audio_sha256,
        sample_rate_hz=run.sample_rate_hz,
        request_configuration=run.request_configuration,
        transport_timings_ms=run.transport_timings_ms,
        estimated_billable_units=run.estimated_billable_units,
        estimated_cost_usd=run.estimated_cost_usd,
        normalized_result=run.normalized_result,
        latency_ms=run.latency_ms,
        created_at=run.created_at,
        status=run.status,
        error_code=run.error_code,
        error_message=run.error_message,
    )


def _pitch_slice(
    acoustic: AcousticRun | None, alignment: AlignmentRun | None, index: int, count: int
) -> dict[str, Any] | None:
    if acoustic is None or acoustic.status != "succeeded" or acoustic.normalized_result is None:
        return None
    points = acoustic.normalized_result.get("mobile_f0")
    if not isinstance(points, list):
        return None
    if count == 1:
        selected = points
    else:
        normalized_alignment = alignment.normalized_result if alignment else None
        quality = normalized_alignment.get("quality") if normalized_alignment else None
        units = normalized_alignment.get("units") if normalized_alignment else None
        if (
            not isinstance(quality, dict)
            or not quality.get("usable_for_syllable_visualization")
            or not isinstance(units, list)
            or index >= len(units)
        ):
            return None
        unit = units[index]
        start = float(unit["start_seconds"])
        end = float(unit["end_seconds"])
        selected = [
            point
            for point in points
            if start <= float(point.get("timestamp_seconds", -1)) <= end
        ]
    values = [
        float(point["normalized_semitones"])
        for point in selected
        if point.get("normalized_semitones") is not None
    ]
    return {
        "pitch_points": selected,
        "change_semitones": round(values[-1] - values[0], 3) if len(values) > 1 else None,
        "voiced_points": len(values),
        "capability_state": "raw_evidence",
    }


class PronunciationLaboratoryService:
    def __init__(self, db: Session, store: AudioObjectStore, settings: Settings) -> None:
        self.db = db
        self.store = store
        self.settings = settings

    def _attempt(self, account_id: uuid.UUID, attempt_id: uuid.UUID) -> PronunciationAttempt:
        attempt = self.db.get(PronunciationAttempt, attempt_id)
        if attempt is None or attempt.account_id != account_id:
            raise AuthorizationError("pronunciation attempt was not found")
        return attempt

    def analyze(
        self,
        *,
        account_id: uuid.UUID,
        attempt_id: uuid.UUID,
        reuse_existing: bool,
        rerun_provider: bool,
        rerun_acoustics: bool,
        rerun_alignment: bool,
    ) -> PronunciationResultResponse:
        attempt = self._attempt(account_id, attempt_id)
        assessment = None
        if reuse_existing and not rerun_provider:
            assessment = _latest(
                self.db,
                AssessmentRun,
                AssessmentRun.account_id == account_id,
                AssessmentRun.pronunciation_attempt_id == attempt_id,
                AssessmentRun.status == "succeeded",
            )
        if assessment is None:
            try:
                assessment = AssessmentService(
                    self.db, self.store, build_assessment_provider(self.settings)
                ).run(account_id=account_id, attempt_id=attempt_id, timeout_seconds=30)
            except BenmaError:
                assessment = _latest(
                    self.db,
                    AssessmentRun,
                    AssessmentRun.account_id == account_id,
                    AssessmentRun.pronunciation_attempt_id == attempt_id,
                )

        analyzer = (
            AutocorrelationAcousticAnalyzer()
            if self.settings.acoustic_provider == "autocorrelation"
            else DisabledAcousticAnalyzer()
        )
        acoustic = AcousticAnalysisService(self.db, self.store, analyzer).run(
            account_id=account_id,
            utterance_id=attempt.utterance_id,
            reuse=reuse_existing and not rerun_acoustics,
        )
        alignment = AlignmentService(
            self.db, self.store, build_aligner(self.settings)
        ).run(
            account_id=account_id,
            attempt_id=attempt_id,
            reuse=reuse_existing and not rerun_alignment,
        )
        PronunciationInterpretationService(self.db, self.settings).run(
            account_id=account_id,
            attempt_id=attempt_id,
            assessment=assessment,
            acoustic=acoustic,
            alignment=alignment,
            reuse=reuse_existing
            and not (rerun_provider or rerun_acoustics or rerun_alignment),
        )
        return self.result(account_id=account_id, attempt_id=attempt_id)

    def result(
        self, *, account_id: uuid.UUID, attempt_id: uuid.UUID
    ) -> PronunciationResultResponse:
        attempt = self._attempt(account_id, attempt_id)
        target = self.db.get(PronunciationTarget, attempt.target_id)
        if target is None or target.account_id != account_id:
            raise AuthorizationError("pronunciation target was not found")
        assessment = _latest(
            self.db,
            AssessmentRun,
            AssessmentRun.account_id == account_id,
            AssessmentRun.pronunciation_attempt_id == attempt_id,
        )
        acoustic = _latest(
            self.db,
            AcousticRun,
            AcousticRun.account_id == account_id,
            AcousticRun.utterance_id == attempt.utterance_id,
        )
        alignment = _latest(
            self.db,
            AlignmentRun,
            AlignmentRun.account_id == account_id,
            AlignmentRun.pronunciation_attempt_id == attempt_id,
        )
        interpretation = _latest(
            self.db,
            PronunciationInterpretationRun,
            PronunciationInterpretationRun.account_id == account_id,
            PronunciationInterpretationRun.pronunciation_attempt_id == attempt_id,
        )
        reference = self.db.scalar(
            select(ReferenceSpeechAsset)
            .where(
                ReferenceSpeechAsset.account_id == account_id,
                ReferenceSpeechAsset.target_id == target.id,
                ReferenceSpeechAsset.status == "succeeded",
            )
            .order_by(ReferenceSpeechAsset.created_at.desc())
        )
        assessment_syllables = (
            assessment.normalized_result.get("syllables", [])
            if assessment and assessment.normalized_result
            else []
        )
        alignment_units = (
            alignment.normalized_result.get("units", [])
            if alignment and alignment.normalized_result
            else []
        )
        observations = interpretation.structured_observations if interpretation else []
        expectation = target.surface_tone_expectation or {}
        surface = expectation.get("expected_surface_tones")
        surface_tones = surface if isinstance(surface, list) else target.lexical_tones
        syllables: list[PronunciationSyllableResult] = []
        for index, pinyin in enumerate(target.pinyin_syllables):
            unit = target.syllable_units[index] if index < len(target.syllable_units) else {}
            provider = (
                assessment_syllables[index]
                if isinstance(assessment_syllables, list) and index < len(assessment_syllables)
                else None
            )
            timing = (
                alignment_units[index]
                if isinstance(alignment_units, list) and index < len(alignment_units)
                else None
            )
            observation = next(
                (item for item in observations if item.get("syllable_index") == index), None
            )
            rules = [
                rule
                for rule in expectation.get("rules", [])
                if rule.get("syllable_index") == index
            ]
            syllables.append(
                PronunciationSyllableResult(
                    syllable_index=index,
                    characters=str(unit.get("characters", target.text[index : index + 1])),
                    pinyin=pinyin,
                    lexical_tone=target.lexical_tones[index],
                    expected_surface_tone=(
                        surface_tones[index] if index < len(surface_tones) else None
                    ),
                    surface_tone_reason=rules,
                    provider_evidence=provider if isinstance(provider, dict) else None,
                    acoustic_evidence=_pitch_slice(
                        acoustic, alignment, index, len(target.pinyin_syllables)
                    ),
                    timing=timing if isinstance(timing, dict) else None,
                    interpretation=observation,
                    capability_state=(
                        str(observation.get("capability_state", "unavailable"))
                        if observation
                        else "unavailable"
                    ),
                )
            )
        statuses = {
            "assessment": assessment.status if assessment else "unavailable",
            "acoustic": acoustic.status if acoustic else "unavailable",
            "alignment": alignment.status if alignment else "unavailable",
            "interpretation": "succeeded" if interpretation else "unavailable",
        }
        overall = {
            "statuses": statuses,
            "provider_scores": assessment.normalized_result if assessment else None,
            "recording_quality": (
                acoustic.normalized_result.get("recording_quality")
                if acoustic and acoustic.normalized_result
                else None
            ),
            "pipeline_latency_ms": sum(
                value
                for value in (
                    assessment.latency_ms if assessment else None,
                    acoustic.latency_ms if acoustic else None,
                    alignment.latency_ms if alignment else None,
                )
                if value is not None
            ),
        }
        return PronunciationResultResponse(
            attempt=PronunciationAttemptResponse.model_validate(attempt),
            target=PronunciationTargetResponse.model_validate(target),
            recording_audio_url=f"/v1/utterances/{attempt.utterance_id}/audio",
            reference_audio=reference_response(reference) if reference else None,
            overall_evidence=overall,
            syllables=syllables,
            assessment=assessment_response(assessment) if assessment else None,
            acoustic=acoustic_response(acoustic) if acoustic else None,
            alignment=alignment_response(alignment) if alignment else None,
            interpretation=(
                interpretation_response(interpretation) if interpretation else None
            ),
            capability_policy={
                "tone_interpretation": (
                    "experimental"
                    if self.settings.enable_experimental_tone_interpretation
                    else "raw_evidence"
                ),
                "categorical_tone_judgment": "unavailable",
                "reference_contour_role": "visual_example_not_grading_truth",
                "intelligibility_inference": "unavailable",
                "provider_candidates": pronunciation_provider_statuses(),
            },
        )

    def reference(
        self,
        *,
        account_id: uuid.UUID,
        target_id: uuid.UUID,
        force: bool,
        timeout_seconds: float,
    ) -> ReferenceSpeechResponse:
        asset = ReferenceSpeechService(self.db, self.store, self.settings).get_or_create(
            account_id=account_id,
            target_id=target_id,
            force=force,
            timeout_seconds=timeout_seconds,
        )
        return reference_response(asset)

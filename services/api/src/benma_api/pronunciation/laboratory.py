"""Pronunciation-laboratory orchestration over immutable evidence runs."""

from __future__ import annotations

import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC
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
from benma_api.errors import AuthorizationError
from benma_api.pronunciation.acoustics import (
    AcousticAnalysisService,
    build_acoustic_analyzer,
)
from benma_api.pronunciation.alignment import (
    AlignmentService,
    build_aligner,
    syllable_labels_match,
    validate_alignment,
)
from benma_api.pronunciation.capabilities import pronunciation_capability_policy
from benma_api.pronunciation.contours import (
    classify_contour,
    display_contour,
    simplify_display,
    syllable_contour,
)
from benma_api.pronunciation.interpretation import (
    PronunciationInterpretationService,
    has_live_assessment,
)
from benma_api.pronunciation.reference import ReferenceSpeechService
from benma_api.pronunciation.service import AssessmentService, log_assessment
from benma_api.pronunciation.timing import resolve_target_timing
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

# Bounded pure provider work; ORM access and all commits stay on the caller thread.
ANALYSIS_WORKERS = ThreadPoolExecutor(max_workers=3, thread_name_prefix="speech-analysis")


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
        acoustic_result={
            **asset.acoustic_result,
            "display_contour": simplify_display(
                display_contour(asset.acoustic_result.get("f0", []))
            ).model_dump(mode="json"),
        }
        if asset.acoustic_result
        else None,
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
            point for point in points if start <= float(point.get("timestamp_seconds", -1)) <= end
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
        started = time.perf_counter()
        # Lock through the final interpretation commit. Duplicate analyze requests
        # recheck reuse after the first transaction, before any provider submission.
        attempt = self.db.scalar(
            select(PronunciationAttempt)
            .where(
                PronunciationAttempt.id == attempt_id,
                PronunciationAttempt.account_id == account_id,
            )
            .with_for_update()
        )
        if attempt is None:
            raise AuthorizationError("pronunciation attempt was not found")
        assessment = None
        if reuse_existing and not rerun_provider:
            assessment = _latest(
                self.db,
                AssessmentRun,
                AssessmentRun.account_id == account_id,
                AssessmentRun.pronunciation_attempt_id == attempt_id,
                AssessmentRun.status == "succeeded",
            )
        assessment_work = (
            None
            if assessment
            else AssessmentService(
                self.db, self.store, build_assessment_provider(self.settings)
            ).prepare(account_id=account_id, attempt_id=attempt_id, timeout_seconds=30)
        )
        analyzer = build_acoustic_analyzer(self.settings)
        acoustic_work = AcousticAnalysisService(self.db, self.store, analyzer).prepare(
            account_id=account_id,
            utterance_id=attempt.utterance_id,
            reuse=reuse_existing and not rerun_acoustics,
        )
        alignment_work = AlignmentService(
            self.db, self.store, build_aligner(self.settings)
        ).prepare(
            account_id=account_id,
            attempt_id=attempt_id,
            reuse=reuse_existing and not rerun_alignment,
        )
        # Only immutable requests, bytes/paths, and provider configuration enter
        # workers. Completion order never selects the evidence used for derivation.
        assessment_future = ANALYSIS_WORKERS.submit(assessment_work) if assessment_work else None
        acoustic_future = ANALYSIS_WORKERS.submit(acoustic_work)
        alignment_future = ANALYSIS_WORKERS.submit(alignment_work)
        if assessment_future:
            assessment, _ = assessment_future.result()
            self.db.add(assessment)
        acoustic = acoustic_future.result()
        alignment = alignment_future.result()
        self.db.add_all([acoustic, alignment])
        self.db.flush()
        derived = PronunciationInterpretationService(self.db, self.settings).run(
            account_id=account_id,
            attempt_id=attempt_id,
            assessment=assessment,
            acoustic=acoustic,
            alignment=alignment,
            reuse=reuse_existing and not (rerun_provider or rerun_acoustics or rerun_alignment),
        )
        self.db.commit()  # Also release locks when an existing interpretation was reused.
        if assessment_future and assessment is not None:
            log_assessment(assessment)
        result = self.result(
            account_id=account_id, attempt_id=attempt_id, interpretation_id=derived.id
        )
        result.overall_evidence["analysis_wall_ms"] = round((time.perf_counter() - started) * 1000)
        return result

    def result(
        self,
        *,
        account_id: uuid.UUID,
        attempt_id: uuid.UUID,
        interpretation_id: uuid.UUID | None = None,
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
        if interpretation_id is not None:
            interpretation = self.db.get(PronunciationInterpretationRun, interpretation_id)
            if (
                interpretation is None
                or interpretation.account_id != account_id
                or interpretation.pronunciation_attempt_id != attempt_id
            ):
                raise AuthorizationError("pronunciation interpretation was not found")
        if interpretation is not None:
            evidence = interpretation.input_evidence_run_ids
            assessment = (
                self.db.get(AssessmentRun, uuid.UUID(evidence["assessment_run_id"]))
                if evidence.get("assessment_run_id")
                else None
            )
            acoustic = (
                self.db.get(AcousticRun, uuid.UUID(evidence["acoustic_run_id"]))
                if evidence.get("acoustic_run_id")
                else None
            )
            alignment = (
                self.db.get(AlignmentRun, uuid.UUID(evidence["alignment_run_id"]))
                if evidence.get("alignment_run_id")
                else None
            )
            if any(
                run is not None and run.account_id != account_id
                for run in (assessment, acoustic, alignment)
            ):
                raise AuthorizationError("pronunciation evidence was not found")
            if (
                (assessment is not None and assessment.pronunciation_attempt_id != attempt_id)
                or (acoustic is not None and acoustic.utterance_id != attempt.utterance_id)
                or (alignment is not None and alignment.pronunciation_attempt_id != attempt_id)
            ):
                raise AuthorizationError("pronunciation evidence lineage was not found")
        reference = self.db.scalar(
            select(ReferenceSpeechAsset)
            .where(
                ReferenceSpeechAsset.account_id == account_id,
                ReferenceSpeechAsset.target_id == target.id,
                ReferenceSpeechAsset.status == "succeeded",
            )
            .order_by(ReferenceSpeechAsset.created_at.desc())
        )
        live_assessment = has_live_assessment(assessment)
        assessment_syllables = (
            assessment.normalized_result.get("syllables", [])
            if assessment and assessment.normalized_result and live_assessment
            else []
        )
        alignment_units = (
            alignment.normalized_result.get("units", [])
            if alignment and alignment.normalized_result
            else []
        )
        observations = interpretation.structured_observations if interpretation else []
        if not live_assessment:
            # Historical immutable runs remain available as raw provenance, but
            # their fixture-derived observations cannot become learner evidence.
            observations = [o for o in observations if o.get("observed_provider_tone") is None]
        expectation = target.surface_tone_expectation or {}
        surface = expectation.get("expected_surface_tones")
        surface_tones = surface if isinstance(surface, list) else [None] * len(target.lexical_tones)
        raw_pitch = (acoustic.normalized_result or {}).get("f0", []) if acoustic else []
        display = display_contour(raw_pitch)
        characters = [str(unit.get("characters", "")) for unit in target.syllable_units]
        timing_resolution = resolve_target_timing(
            alignment.normalized_result or {} if alignment else {},
            status=alignment.status if alignment else "unavailable",
            characters=characters,
            readings=target.pinyin_syllables,
            acoustic=acoustic.normalized_result or {} if acoustic else {},
        )
        timing_resolution.update(
            {
                "source_record_type": "AlignmentRun",
                "source_record_id": str(alignment.id) if alignment else None,
                "available_at": alignment.created_at.isoformat() if alignment else None,
                "acoustics_before_timing": bool(
                    acoustic
                    and alignment
                    and acoustic.created_at.replace(tzinfo=UTC)
                    < alignment.created_at.replace(tzinfo=UTC)
                ),
            }
        )
        timing_usable = bool(timing_resolution["accepted"])
        # Reuse real provider syllable/one-character word timestamps when forced
        # alignment is absent. Multi-character word spans are never partitioned.
        if not timing_usable and assessment and assessment.normalized_result and acoustic:
            provider_units = [
                {"label": item.get("text", ""), **item["timing"], "source": "assessment"}
                for item in assessment_syllables
                if isinstance(item, dict)
                and isinstance(item.get("timing"), dict)
                and isinstance(item["timing"].get("start_seconds"), (int, float))
                and isinstance(item["timing"].get("end_seconds"), (int, float))
            ]
            duration = (acoustic.normalized_result or {}).get("duration_seconds", 0)
            if (
                assessment.normalized_result.get("evidence_status") != "synthetic_replay"
                and syllable_labels_match(provider_units, characters, target.pinyin_syllables)
                and validate_alignment(
                    provider_units, target_count=len(characters), duration_seconds=duration
                )["usable_for_syllable_visualization"]
            ):
                alignment_units, timing_usable = provider_units, True
                timing_resolution.update(
                    {
                        "accepted": True,
                        "reason": "validated_assessment_span",
                        "source_record_type": "AssessmentRun",
                        "source_record_id": str(assessment.id),
                        "available_at": assessment.created_at.isoformat(),
                        "sources": ["assessment"],
                    }
                )
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
                rule for rule in expectation.get("rules", []) if rule.get("syllable_index") == index
            ]
            slice_display = (
                syllable_contour(display, timing["start_seconds"], timing["end_seconds"])
                if timing_usable and isinstance(timing, dict)
                else None
            )
            measured = (
                classify_contour(
                    slice_display, timing["start_seconds"], timing["end_seconds"], raw=raw_pitch
                )
                if slice_display is not None and isinstance(timing, dict)
                else None
            )
            syllables.append(
                PronunciationSyllableResult(
                    display_contour=simplify_display(
                        slice_display,
                        preserve_seconds=measured.features.get("first_reliable_core_seconds")
                        if measured
                        else None,
                    )
                    if slice_display
                    else None,
                    **(
                        {"observed_contour": measured}
                        if slice_display is not None and isinstance(timing, dict)
                        else {}
                    ),
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
            "timing_resolution": timing_resolution,
            "provider_scores": assessment.normalized_result if assessment else None,
            "recording_quality": (
                acoustic.normalized_result.get("recording_quality")
                if acoustic and acoustic.normalized_result
                else None
            ),
            "provider_compute_sum_ms": sum(
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
            # More detail promises every retained frame and measured gap.
            display_contour=display,
            attempt=PronunciationAttemptResponse.model_validate(attempt),
            target=PronunciationTargetResponse.model_validate(target),
            recording_audio_url=f"/v1/utterances/{attempt.utterance_id}/audio",
            reference_audio=reference_response(reference) if reference else None,
            overall_evidence=overall,
            syllables=syllables,
            assessment=assessment_response(assessment) if assessment else None,
            acoustic=acoustic_response(acoustic) if acoustic else None,
            alignment=alignment_response(alignment) if alignment else None,
            interpretation=(interpretation_response(interpretation) if interpretation else None),
            capability_policy=pronunciation_capability_policy(self.settings),
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

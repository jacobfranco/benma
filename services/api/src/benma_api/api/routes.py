"""Deliberately small resource-oriented API surface."""

from __future__ import annotations

import uuid
from functools import partial
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from benma_api.api.blocking import run_bounded_speech_work
from benma_api.audio.service import AudioIngestService
from benma_api.auth.service import (
    AuthContext,
    create_dev_session,
    get_auth_context,
    revoke_session,
)
from benma_api.config import Settings, get_request_settings
from benma_api.db.models import (
    AssessmentRun,
    AudioAsset,
    PerceptionRun,
    PracticeSession,
    PronunciationAttempt,
    PronunciationTarget,
    ReferenceSpeechAsset,
    UserCorrection,
    Utterance,
)
from benma_api.db.session import get_db
from benma_api.errors import AuthorizationError, InvalidAudioError, InvalidTargetError
from benma_api.perception.repository import SqlPerceptionRepository
from benma_api.perception.service import PerceptionService
from benma_api.pronunciation.laboratory import PronunciationLaboratoryService
from benma_api.pronunciation.service import AssessmentService
from benma_api.pronunciation.targets import parse_corrected_pinyin, parse_mandarin_target
from benma_api.schemas import (
    AccountResponse,
    AssessmentRequest,
    AssessmentRunResponse,
    AttemptComparisonRequest,
    AttemptComparisonResponse,
    AudioAssetResponse,
    AuthTokenResponse,
    DevAuthRequest,
    PerceptionRunResponse,
    PinyinCorrectionCreate,
    PracticeSessionCreate,
    PracticeSessionResponse,
    PronunciationAnalyzeRequest,
    PronunciationAttemptCreate,
    PronunciationAttemptResponse,
    PronunciationResultResponse,
    PronunciationTargetCreate,
    PronunciationTargetResponse,
    ReferenceSpeechRequestBody,
    ReferenceSpeechResponse,
    UnknownPerceptionRequest,
    UserCorrectionCreate,
    UserCorrectionResponse,
    UtteranceResponse,
)
from benma_api.speech.providers.factory import (
    build_assessment_provider,
    build_perception_provider,
)
from benma_api.storage.audio_store import AudioObjectStore, get_audio_store

router = APIRouter()
dev_router = APIRouter()


def audio_response(asset: AudioAsset) -> AudioAssetResponse:
    return AudioAssetResponse(
        id=asset.id,
        kind=asset.kind,
        mime_type=asset.mime_type,
        sha256=asset.sha256,
        size_bytes=asset.size_bytes,
        sample_rate_hz=asset.sample_rate_hz,
        channels=asset.channels,
        sample_width_bits=asset.sample_width_bits,
        duration_seconds=asset.duration_seconds,
    )


def utterance_response(db: Session, utterance: Utterance) -> UtteranceResponse:
    original = db.get(AudioAsset, utterance.original_audio_asset_id)
    canonical = db.get(AudioAsset, utterance.canonical_audio_asset_id)
    if original is None or canonical is None:
        raise RuntimeError("utterance has missing audio assets")
    return UtteranceResponse(
        id=utterance.id,
        account_id=utterance.account_id,
        practice_session_id=utterance.practice_session_id,
        created_at=utterance.created_at,
        original_audio=audio_response(original),
        canonical_audio=audio_response(canonical),
        audio_url=f"/v1/utterances/{utterance.id}/audio",
    )


def practice_response(practice: PracticeSession) -> PracticeSessionResponse:
    return PracticeSessionResponse(
        id=practice.id,
        account_id=practice.account_id,
        mode=practice.mode,
        started_at=practice.started_at,
        ended_at=practice.ended_at,
        metadata=practice.session_metadata,
    )


def perception_response(run: PerceptionRun) -> PerceptionRunResponse:
    return PerceptionRunResponse(
        id=run.id,
        utterance_id=run.utterance_id,
        provider=run.provider,
        product=run.product,
        provider_version=run.provider_version,
        adapter_version=run.adapter_version,
        transcript=run.transcript,
        alternatives=run.alternatives,
        provider_uncertainty=run.provider_uncertainty,
        normalized_result=run.normalized_result,
        latency_ms=run.latency_ms,
        created_at=run.created_at,
        status=run.status,
        error_code=run.error_code,
        error_message=run.error_message,
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


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@dev_router.post("/v1/dev/auth", response_model=AuthTokenResponse)
async def dev_auth(
    body: DevAuthRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_request_settings),
) -> AuthTokenResponse:
    account, auth_session, token = create_dev_session(db, settings, body.phone_number)
    return AuthTokenResponse(
        token=token, expires_at=auth_session.expires_at, account_id=account.id
    )


@router.get("/v1/me", response_model=AccountResponse)
async def me(auth: AuthContext = Depends(get_auth_context)) -> AccountResponse:
    return AccountResponse.model_validate(auth.account)


@router.delete("/v1/auth/session", status_code=status.HTTP_204_NO_CONTENT)
async def delete_auth_session(
    auth: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)
) -> Response:
    revoke_session(db, auth)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/v1/practice-sessions",
    response_model=PracticeSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_practice_session(
    body: PracticeSessionCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> PracticeSessionResponse:
    practice = PracticeSession(
        account_id=auth.account_id,
        mode=body.mode,
        session_metadata=body.metadata,
    )
    db.add(practice)
    db.commit()
    return practice_response(practice)


@router.get("/v1/practice-sessions/{session_id}", response_model=PracticeSessionResponse)
async def get_practice_session(
    session_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> PracticeSessionResponse:
    practice = db.get(PracticeSession, session_id)
    if practice is None or practice.account_id != auth.account_id:
        raise AuthorizationError("practice session was not found")
    return practice_response(practice)


@router.post(
    "/v1/utterances",
    response_model=UtteranceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_utterance(
    file: Annotated[UploadFile, File()],
    practice_session_id: Annotated[uuid.UUID | None, Form()] = None,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_request_settings),
    store: AudioObjectStore = Depends(get_audio_store),
) -> UtteranceResponse:
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise InvalidAudioError("audio upload exceeds the configured size limit")
    utterance = await run_bounded_speech_work(
        settings,
        partial(
            AudioIngestService(db, store, settings).ingest,
            account_id=auth.account_id,
            data=data,
            mime_type=file.content_type or "application/octet-stream",
            practice_session_id=practice_session_id,
        ),
    )
    return utterance_response(db, utterance)


@router.get("/v1/utterances", response_model=list[UtteranceResponse])
async def list_utterances(
    auth: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)
) -> list[UtteranceResponse]:
    utterances = db.scalars(
        select(Utterance)
        .where(Utterance.account_id == auth.account_id)
        .order_by(Utterance.created_at.desc())
        .limit(100)
    )
    return [utterance_response(db, item) for item in utterances]


@router.get("/v1/utterances/{utterance_id}", response_model=UtteranceResponse)
async def get_utterance(
    utterance_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> UtteranceResponse:
    utterance = db.get(Utterance, utterance_id)
    if utterance is None or utterance.account_id != auth.account_id:
        raise AuthorizationError("utterance was not found")
    return utterance_response(db, utterance)


@router.get("/v1/utterances/{utterance_id}/audio")
async def get_utterance_audio(
    utterance_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    store: AudioObjectStore = Depends(get_audio_store),
) -> Response:
    utterance = db.get(Utterance, utterance_id)
    if utterance is None or utterance.account_id != auth.account_id:
        raise AuthorizationError("utterance was not found")
    asset = db.get(AudioAsset, utterance.original_audio_asset_id)
    if asset is None or asset.account_id != auth.account_id:
        raise AuthorizationError("audio was not found")
    return Response(
        content=store.read(asset.storage_key),
        media_type=asset.mime_type,
        headers={"Cache-Control": "private, no-store"},
    )


@router.post(
    "/v1/utterances/{utterance_id}/perceptions",
    response_model=PerceptionRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_perception(
    utterance_id: uuid.UUID,
    body: UnknownPerceptionRequest,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_request_settings),
    store: AudioObjectStore = Depends(get_audio_store),
) -> PerceptionRunResponse:
    service = PerceptionService(
        SqlPerceptionRepository(db), store, build_perception_provider(settings)
    )
    return perception_response(
        await run_bounded_speech_work(
            settings,
            partial(
                service.run,
                account_id=auth.account_id,
                utterance_id=utterance_id,
                language_hint=body.language_hint,
                timeout_seconds=body.timeout_seconds,
            ),
        )
    )


@router.get("/v1/perceptions/{run_id}", response_model=PerceptionRunResponse)
async def get_perception(
    run_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> PerceptionRunResponse:
    run = db.get(PerceptionRun, run_id)
    if run is None or run.account_id != auth.account_id:
        raise AuthorizationError("perception run was not found")
    return perception_response(run)


@router.post(
    "/v1/utterances/{utterance_id}/corrections",
    response_model=UserCorrectionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_correction(
    utterance_id: uuid.UUID,
    body: UserCorrectionCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> UserCorrectionResponse:
    utterance = db.get(Utterance, utterance_id)
    if utterance is None or utterance.account_id != auth.account_id:
        raise AuthorizationError("utterance was not found")
    if body.perception_run_id is not None:
        run = db.get(PerceptionRun, body.perception_run_id)
        if (
            run is None
            or run.account_id != auth.account_id
            or run.utterance_id != utterance_id
        ):
            raise AuthorizationError("perception run was not found")
    correction = UserCorrection(
        account_id=auth.account_id,
        utterance_id=utterance_id,
        perception_run_id=body.perception_run_id,
        intended_text=body.intended_text,
    )
    db.add(correction)
    db.commit()
    return UserCorrectionResponse.model_validate(correction)


@router.post(
    "/v1/pronunciation-targets",
    response_model=PronunciationTargetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_pronunciation_target(
    body: PronunciationTargetCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> PronunciationTargetResponse:
    parsed = parse_mandarin_target(body.text)
    target = PronunciationTarget(
        account_id=auth.account_id,
        text=body.text,
        display_pinyin=parsed.display_pinyin,
        pinyin_syllables=parsed.pinyin_syllables,
        lexical_tones=parsed.lexical_tones,
        target_source=body.target_source,
        pinyin_source=parsed.provenance,
        pinyin_alternatives=parsed.alternatives,
        syllable_units=parsed.syllable_units,
        surface_tone_expectation=parsed.surface_tone_expectation,
    )
    db.add(target)
    db.commit()
    return PronunciationTargetResponse.model_validate(target)


@router.post(
    "/v1/pronunciation-targets/{target_id}/pinyin-corrections",
    response_model=PronunciationTargetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def correct_pronunciation_target(
    target_id: uuid.UUID,
    body: PinyinCorrectionCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> PronunciationTargetResponse:
    original = db.get(PronunciationTarget, target_id)
    if original is None or original.account_id != auth.account_id:
        raise AuthorizationError("pronunciation target was not found")
    try:
        parsed = parse_corrected_pinyin(original.text, body.pinyin)
    except ValueError as exc:
        raise InvalidTargetError(str(exc)) from exc
    corrected = PronunciationTarget(
        account_id=auth.account_id,
        text=original.text,
        display_pinyin=parsed.display_pinyin,
        pinyin_syllables=parsed.pinyin_syllables,
        lexical_tones=parsed.lexical_tones,
        target_source=original.target_source,
        pinyin_source=parsed.provenance,
        pinyin_alternatives=parsed.alternatives,
        syllable_units=parsed.syllable_units,
        surface_tone_expectation=parsed.surface_tone_expectation,
        parent_target_id=original.id,
    )
    db.add(corrected)
    db.commit()
    return PronunciationTargetResponse.model_validate(corrected)


@router.post(
    "/v1/pronunciation-targets/{target_id}/reference-speech",
    response_model=ReferenceSpeechResponse,
)
async def create_reference_speech(
    target_id: uuid.UUID,
    body: ReferenceSpeechRequestBody,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_request_settings),
    store: AudioObjectStore = Depends(get_audio_store),
) -> ReferenceSpeechResponse:
    service = PronunciationLaboratoryService(db, store, settings)
    return await run_bounded_speech_work(
        settings,
        partial(
            service.reference,
            account_id=auth.account_id,
            target_id=target_id,
            force=body.force,
            timeout_seconds=body.timeout_seconds,
        ),
    )


@router.get("/v1/reference-speech/{reference_id}/audio")
async def get_reference_speech_audio(
    reference_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    store: AudioObjectStore = Depends(get_audio_store),
) -> Response:
    reference = db.get(ReferenceSpeechAsset, reference_id)
    if (
        reference is None
        or reference.account_id != auth.account_id
        or reference.audio_asset_id is None
        or reference.status != "succeeded"
    ):
        raise AuthorizationError("reference speech was not found")
    asset = db.get(AudioAsset, reference.audio_asset_id)
    if asset is None or asset.account_id != auth.account_id:
        raise AuthorizationError("reference audio was not found")
    return Response(
        content=store.read(asset.storage_key),
        media_type=asset.mime_type,
        headers={"Cache-Control": "private, max-age=31536000, immutable"},
    )


@router.get(
    "/v1/pronunciation-targets/{target_id}", response_model=PronunciationTargetResponse
)
async def get_pronunciation_target(
    target_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> PronunciationTargetResponse:
    target = db.get(PronunciationTarget, target_id)
    if target is None or target.account_id != auth.account_id:
        raise AuthorizationError("pronunciation target was not found")
    return PronunciationTargetResponse.model_validate(target)


@router.post(
    "/v1/pronunciation-attempts",
    response_model=PronunciationAttemptResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_pronunciation_attempt(
    body: PronunciationAttemptCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> PronunciationAttemptResponse:
    utterance = db.get(Utterance, body.utterance_id)
    target = db.get(PronunciationTarget, body.target_id)
    if (
        utterance is None
        or utterance.account_id != auth.account_id
        or target is None
        or target.account_id != auth.account_id
    ):
        raise AuthorizationError("target or utterance was not found")
    attempt = PronunciationAttempt(
        account_id=auth.account_id,
        utterance_id=body.utterance_id,
        target_id=body.target_id,
    )
    db.add(attempt)
    db.commit()
    return PronunciationAttemptResponse.model_validate(attempt)


@router.get(
    "/v1/pronunciation-attempts/{attempt_id}", response_model=PronunciationAttemptResponse
)
async def get_pronunciation_attempt(
    attempt_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> PronunciationAttemptResponse:
    attempt = db.get(PronunciationAttempt, attempt_id)
    if attempt is None or attempt.account_id != auth.account_id:
        raise AuthorizationError("pronunciation attempt was not found")
    return PronunciationAttemptResponse.model_validate(attempt)


@router.post(
    "/v1/pronunciation-attempts/{attempt_id}/assessments",
    response_model=AssessmentRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_assessment(
    attempt_id: uuid.UUID,
    body: AssessmentRequest,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_request_settings),
    store: AudioObjectStore = Depends(get_audio_store),
) -> AssessmentRunResponse:
    service = AssessmentService(db, store, build_assessment_provider(settings))
    return assessment_response(
        await run_bounded_speech_work(
            settings,
            partial(
                service.run,
                account_id=auth.account_id,
                attempt_id=attempt_id,
                timeout_seconds=body.timeout_seconds,
            ),
        )
    )


@router.post(
    "/v1/pronunciation-attempts/{attempt_id}/analyze",
    response_model=PronunciationResultResponse,
)
async def analyze_pronunciation_attempt(
    attempt_id: uuid.UUID,
    body: PronunciationAnalyzeRequest,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_request_settings),
    store: AudioObjectStore = Depends(get_audio_store),
) -> PronunciationResultResponse:
    service = PronunciationLaboratoryService(db, store, settings)
    return await run_bounded_speech_work(
        settings,
        partial(
            service.analyze,
            account_id=auth.account_id,
            attempt_id=attempt_id,
            reuse_existing=body.reuse_existing,
            rerun_provider=body.rerun_provider,
            rerun_acoustics=body.rerun_acoustics,
            rerun_alignment=body.rerun_alignment,
        ),
    )


@router.get(
    "/v1/pronunciation-attempts/{attempt_id}/result",
    response_model=PronunciationResultResponse,
)
async def get_pronunciation_result(
    attempt_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_request_settings),
    store: AudioObjectStore = Depends(get_audio_store),
) -> PronunciationResultResponse:
    return PronunciationLaboratoryService(db, store, settings).result(
        account_id=auth.account_id, attempt_id=attempt_id
    )


@router.get(
    "/v1/pronunciation-targets/{target_id}/attempts",
    response_model=list[PronunciationResultResponse],
)
async def list_pronunciation_attempts(
    target_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_request_settings),
    store: AudioObjectStore = Depends(get_audio_store),
) -> list[PronunciationResultResponse]:
    target = db.get(PronunciationTarget, target_id)
    if target is None or target.account_id != auth.account_id:
        raise AuthorizationError("pronunciation target was not found")
    attempts = db.scalars(
        select(PronunciationAttempt)
        .where(
            PronunciationAttempt.account_id == auth.account_id,
            PronunciationAttempt.target_id == target_id,
        )
        .order_by(PronunciationAttempt.created_at.asc())
        .limit(100)
    )
    service = PronunciationLaboratoryService(db, store, settings)
    return [service.result(account_id=auth.account_id, attempt_id=item.id) for item in attempts]


@router.post(
    "/v1/pronunciation-attempts/compare",
    response_model=AttemptComparisonResponse,
)
async def compare_pronunciation_attempts(
    body: AttemptComparisonRequest,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_request_settings),
    store: AudioObjectStore = Depends(get_audio_store),
) -> AttemptComparisonResponse:
    service = PronunciationLaboratoryService(db, store, settings)
    return AttemptComparisonResponse(
        first=service.result(account_id=auth.account_id, attempt_id=body.first_attempt_id),
        second=service.result(account_id=auth.account_id, attempt_id=body.second_attempt_id),
        disclaimer="Evidence is shown side by side; Benma does not calculate an improvement score.",
    )

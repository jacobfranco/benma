"""Deliberately small resource-oriented API surface."""

from __future__ import annotations

import asyncio
import threading
import uuid
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from functools import partial
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from benma_api.api.blocking import run_bounded_analysis_work, run_bounded_speech_work
from benma_api.assistant_generation.contracts import AssistantResponseGenerationPort
from benma_api.assistant_generation.factory import build_assistant_response_generator
from benma_api.assistant_speech.factory import build_assistant_speech_provider
from benma_api.assistant_speech.repository import SqlAssistantSpeechRepository
from benma_api.assistant_speech.service import AssistantSpeechService
from benma_api.audio.service import AudioIngestService
from benma_api.auth.service import (
    AuthContext,
    create_dev_session,
    get_auth_context,
    revoke_session,
)
from benma_api.config import Settings, get_request_settings
from benma_api.contextual_interpretation.contracts import ContextualInterpretationPort
from benma_api.contextual_interpretation.factory import build_contextual_interpreter
from benma_api.contextual_interpretation.repository import (
    SqlContextualInterpretationRepository,
)
from benma_api.contextual_interpretation.service import ContextualInterpretationService
from benma_api.conversation.context import resolved_turn_text
from benma_api.conversation.repository import SqlConversationRepository
from benma_api.conversation.service import ConversationService
from benma_api.db.models import (
    AssessmentRun,
    AssistantGenerationRun,
    AssistantSpeechRun,
    AudioAsset,
    ContextualInterpretationRun,
    ConversationTurn,
    PerceivedSpeechAnalysis,
    PerceptionRun,
    PracticeSession,
    PronunciationAttempt,
    PronunciationTarget,
    ReferenceSpeechAsset,
    UserCorrection,
    Utterance,
)
from benma_api.db.session import get_db
from benma_api.errors import (
    AuthorizationError,
    BenmaError,
    InvalidAudioError,
    InvalidTargetError,
)
from benma_api.perception.repository import SqlPerceptionRepository
from benma_api.perception.service import PerceptionService
from benma_api.pronunciation.acoustics import (
    AcousticAnalysisService,
    build_acoustic_analyzer,
)
from benma_api.pronunciation.laboratory import PronunciationLaboratoryService, acoustic_response
from benma_api.pronunciation.perceived import (
    PerceivedSpeechAnalysisService,
    analysis_response,
    reading_response,
)
from benma_api.pronunciation.service import AssessmentService
from benma_api.pronunciation.targets import parse_corrected_pinyin, parse_mandarin_target
from benma_api.pronunciation.warmup import start_acoustic_warmup
from benma_api.schemas import (
    AccountResponse,
    AcousticRunResponse,
    AssessmentRequest,
    AssessmentRunResponse,
    AssistantGenerationRunResponse,
    AssistantSpeechCreate,
    AssistantSpeechRunResponse,
    AttemptComparisonRequest,
    AttemptComparisonResponse,
    AudioAssetResponse,
    AuthTokenResponse,
    ContextualInterpretationCreate,
    ContextualInterpretationRunResponse,
    ConversationCreate,
    ConversationResponse,
    ConversationStreamEvent,
    ConversationTurnResponse,
    DevAuthRequest,
    FreeTalkTurnResponse,
    PerceivedAnalysisCreate,
    PerceivedReadingResponse,
    PerceivedSpeechAnalysisResponse,
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
    UserConversationTurnCreate,
    UserCorrectionCreate,
    UserCorrectionResponse,
    UtteranceResponse,
)
from benma_api.speech.providers.factory import (
    build_assessment_provider,
    build_perception_provider,
)
from benma_api.speech.synthesis import SpeechSynthesisPort
from benma_api.storage.audio_store import AudioObjectStore, get_audio_store

router = APIRouter()
dev_router = APIRouter()
CONVERSATION_WORKERS = ThreadPoolExecutor(max_workers=2, thread_name_prefix="conversation")


async def get_contextual_interpreter(
    settings: Settings = Depends(get_request_settings),
) -> ContextualInterpretationPort:
    return build_contextual_interpreter(settings)


async def get_assistant_response_generator(
    settings: Settings = Depends(get_request_settings),
) -> AssistantResponseGenerationPort:
    return build_assistant_response_generator(settings)


async def get_assistant_speech_provider(
    settings: Settings = Depends(get_request_settings),
) -> SpeechSynthesisPort:
    return build_assistant_speech_provider(settings)


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


def conversation_turn_response(db: Session, turn: ConversationTurn) -> ConversationTurnResponse:
    perception = (
        db.get(PerceptionRun, turn.perception_run_id)
        if turn.perception_run_id is not None
        else None
    )
    interpretation = (
        db.get(ContextualInterpretationRun, turn.contextual_interpretation_run_id)
        if turn.contextual_interpretation_run_id is not None
        else None
    )
    generation = (
        db.get(AssistantGenerationRun, turn.assistant_generation_run_id)
        if turn.assistant_generation_run_id is not None
        else None
    )
    speech = (
        SqlAssistantSpeechRepository(db).latest_for_turn(turn.account_id, turn.id)
        if turn.role == "assistant"
        else None
    )
    if perception is not None and (
        perception.account_id != turn.account_id or perception.utterance_id != turn.utterance_id
    ):
        raise RuntimeError("conversation turn has mismatched perception evidence")
    if interpretation is not None and (
        interpretation.account_id != turn.account_id
        or interpretation.perception_run_id != turn.perception_run_id
    ):
        raise RuntimeError("conversation turn has mismatched contextual evidence")
    if generation is not None and (
        generation.account_id != turn.account_id
        or generation.conversation_id != turn.conversation_id
        or generation.generated_text != turn.assistant_text
    ):
        raise RuntimeError("conversation turn has mismatched assistant generation evidence")
    if speech is not None and (
        speech.account_id != turn.account_id
        or speech.conversation_id != turn.conversation_id
        or speech.assistant_generation_run_id != turn.assistant_generation_run_id
        or speech.assistant_turn_id != turn.id
        or speech.text_snapshot != turn.assistant_text
    ):
        raise RuntimeError("conversation turn has mismatched assistant speech evidence")
    return ConversationTurnResponse(
        id=turn.id,
        conversation_id=turn.conversation_id,
        account_id=turn.account_id,
        sequence_number=turn.sequence_number,
        role=turn.role,
        assistant_text=turn.assistant_text,
        perceived_text=perception.transcript if perception else None,
        interpretation_decision=interpretation.decision if interpretation else None,
        resolved_text=resolved_turn_text(
            turn,
            perception=perception,
            interpretation=interpretation,
        ),
        utterance_id=turn.utterance_id,
        perception_run_id=turn.perception_run_id,
        contextual_interpretation_run_id=turn.contextual_interpretation_run_id,
        assistant_generation_run_id=turn.assistant_generation_run_id,
        assistant_speech=(assistant_speech_response(db, speech) if speech else None),
        created_at=turn.created_at,
    )


def assistant_speech_response(db: Session, run: AssistantSpeechRun) -> AssistantSpeechRunResponse:
    audio = db.get(AudioAsset, run.audio_asset_id) if run.audio_asset_id else None
    if audio is not None and audio.account_id != run.account_id:
        raise RuntimeError("assistant speech has mismatched audio evidence")
    if (run.status == "succeeded") != (audio is not None):
        raise RuntimeError("assistant speech status does not match audio evidence")
    return AssistantSpeechRunResponse(
        id=run.id,
        account_id=run.account_id,
        conversation_id=run.conversation_id,
        assistant_generation_run_id=run.assistant_generation_run_id,
        assistant_turn_id=run.assistant_turn_id,
        provider=run.provider,
        product=run.product,
        provider_version=run.provider_version,
        adapter_version=run.adapter_version,
        model=run.model,
        voice=run.voice,
        locale=run.locale,
        generation_configuration=run.generation_configuration,
        text_snapshot=run.text_snapshot,
        audio_asset=audio_response(audio) if audio else None,
        audio_url=(f"/v1/assistant-speeches/{run.id}/audio" if audio else None),
        latency_ms=run.latency_ms,
        status=run.status,
        error_code=run.error_code,
        error_message=run.error_message,
        created_at=run.created_at,
    )


def assistant_generation_response(
    run: AssistantGenerationRun,
) -> AssistantGenerationRunResponse:
    return AssistantGenerationRunResponse(
        id=run.id,
        account_id=run.account_id,
        conversation_id=run.conversation_id,
        triggering_user_turn_id=run.triggering_user_turn_id,
        provider=run.provider,
        product=run.product,
        provider_version=run.provider_version,
        adapter_version=run.adapter_version,
        model=run.model,
        generator_version=run.generator_version,
        generator_configuration=run.generator_configuration,
        generation_type=run.generation_type,
        input_snapshot=run.input_snapshot,
        generated_text=run.generated_text,
        normalized_result=run.normalized_result,
        latency_ms=run.latency_ms,
        created_at=run.created_at,
        status=run.status,
        error_code=run.error_code,
        error_message=run.error_message,
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


def contextual_interpretation_response(
    run: ContextualInterpretationRun,
) -> ContextualInterpretationRunResponse:
    return ContextualInterpretationRunResponse(
        id=run.id,
        perception_run_id=run.perception_run_id,
        interpreter=run.interpreter,
        interpreter_version=run.interpreter_version,
        interpreter_configuration=run.interpreter_configuration,
        context_snapshot=run.context_snapshot,
        decision=run.decision,
        inferred_text=run.inferred_text,
        uncertainty=run.uncertainty,
        clarification_needed=run.clarification_needed,
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
    return AuthTokenResponse(token=token, expires_at=auth_session.expires_at, account_id=account.id)


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
    "/v1/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    body: ConversationCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ConversationResponse:
    del body
    conversation = ConversationService(db).create(account_id=auth.account_id)
    return ConversationResponse.model_validate(conversation)


@router.get("/v1/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ConversationResponse:
    conversation = SqlConversationRepository(db).load_conversation(auth.account_id, conversation_id)
    if conversation is None:
        raise AuthorizationError("conversation was not found")
    return ConversationResponse.model_validate(conversation)


@router.get(
    "/v1/conversations/{conversation_id}/turns",
    response_model=list[ConversationTurnResponse],
)
async def list_conversation_turns(
    conversation_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[ConversationTurnResponse]:
    repository = SqlConversationRepository(db)
    conversation = repository.load_conversation(auth.account_id, conversation_id)
    if conversation is None:
        raise AuthorizationError("conversation was not found")
    return [
        conversation_turn_response(db, turn)
        for turn in repository.list_turns(auth.account_id, conversation.id)
    ]


@router.post(
    "/v1/conversations/{conversation_id}/user-turns",
    response_model=FreeTalkTurnResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_conversation_turn(
    conversation_id: uuid.UUID,
    body: UserConversationTurnCreate,
    response: Response,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_request_settings),
    interpreter: ContextualInterpretationPort = Depends(get_contextual_interpreter),
    generator: AssistantResponseGenerationPort = Depends(get_assistant_response_generator),
) -> FreeTalkTurnResponse:
    result = await run_bounded_speech_work(
        settings,
        partial(
            ConversationService(db).add_user_turn,
            account_id=auth.account_id,
            conversation_id=conversation_id,
            utterance_id=body.utterance_id,
            perception_run_id=body.perception_run_id,
            interpreter=interpreter,
            generator=generator,
        ),
    )
    if settings.environment == "development":
        response.headers["Server-Timing"] = (
            f"interpretation;dur={result.interpretation_ms},generation;dur={result.generation_ms}"
        )
    user_response = conversation_turn_response(db, result.user_turn)
    return FreeTalkTurnResponse(
        **user_response.model_dump(),
        assistant_turn=conversation_turn_response(db, result.assistant_turn),
    )


@router.post(
    "/v1/conversations/{conversation_id}/user-turns/stream",
    response_model=ConversationStreamEvent,
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "One ConversationStreamEvent JSON object per line.",
            "content": {
                "application/x-ndjson": {
                    "schema": {"$ref": "#/components/schemas/ConversationStreamEvent"},
                }
            },
        }
    },
)
async def stream_user_conversation_turn(
    conversation_id: uuid.UUID,
    body: UserConversationTurnCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    interpreter: ContextualInterpretationPort = Depends(get_contextual_interpreter),
    generator: AssistantResponseGenerationPort = Depends(get_assistant_response_generator),
) -> StreamingResponse:
    """Authoritative progress without splitting the atomic conversation transaction."""
    account_id = auth.account_id
    repository = SqlConversationRepository(db)
    if repository.load_conversation(account_id, conversation_id) is None:
        raise AuthorizationError("conversation was not found")
    if (
        repository.load_user_evidence(
            account_id, utterance_id=body.utterance_id, perception_run_id=body.perception_run_id
        )
        is None
    ):
        raise AuthorizationError("utterance or perception run was not found")
    bind = db.get_bind()
    db.rollback()  # End the read-only preflight before opening the worker's session.

    async def events() -> AsyncIterator[str]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[ConversationStreamEvent | None] = asyncio.Queue()
        disconnected = threading.Event()

        def deliver(event: ConversationStreamEvent | None) -> None:
            if not disconnected.is_set():
                # The request may have ended; the authorized transaction may finish.
                with suppress(RuntimeError):
                    loop.call_soon_threadsafe(queue.put_nowait, event)

        def work() -> None:
            # The worker owns this session for its whole lifetime. A disconnect
            # never closes another thread's transaction or repeats provider calls.
            try:
                with Session(bind=bind, expire_on_commit=False) as worker_db:
                    result = ConversationService(worker_db).add_user_turn(
                        account_id=account_id,
                        conversation_id=conversation_id,
                        utterance_id=body.utterance_id,
                        perception_run_id=body.perception_run_id,
                        interpreter=interpreter,
                        generator=generator,
                        on_interpretation=lambda run, elapsed: deliver(
                            ConversationStreamEvent(
                                type="interpretation",
                                interpretation=contextual_interpretation_response(run),
                                interpretation_ms=elapsed,
                            )
                        ),
                    )
                    deliver(
                        ConversationStreamEvent(
                            type="complete",
                            result=FreeTalkTurnResponse(
                                **conversation_turn_response(
                                    worker_db, result.user_turn
                                ).model_dump(),
                                assistant_turn=conversation_turn_response(
                                    worker_db, result.assistant_turn
                                ),
                            ),
                            generation_ms=result.generation_ms,
                        )
                    )
            except Exception as exc:
                deliver(
                    ConversationStreamEvent(
                        type="error",
                        error_code=exc.code if isinstance(exc, BenmaError) else "internal_failure",
                    )
                )
            finally:
                deliver(None)

        CONVERSATION_WORKERS.submit(work)
        try:
            while (event := await queue.get()) is not None:
                yield event.model_dump_json() + "\n"
        finally:
            disconnected.set()

    return StreamingResponse(
        events(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


@router.get(
    "/v1/assistant-generations/{run_id}",
    response_model=AssistantGenerationRunResponse,
)
async def get_assistant_generation(
    run_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> AssistantGenerationRunResponse:
    run = db.get(AssistantGenerationRun, run_id)
    if run is None or run.account_id != auth.account_id:
        raise AuthorizationError("assistant generation run was not found")
    return assistant_generation_response(run)


@router.post(
    "/v1/assistant-generations/{run_id}/speech",
    response_model=AssistantSpeechRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_assistant_speech(
    run_id: uuid.UUID,
    body: AssistantSpeechCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_request_settings),
    provider: SpeechSynthesisPort = Depends(get_assistant_speech_provider),
    store: AudioObjectStore = Depends(get_audio_store),
) -> AssistantSpeechRunResponse:
    del body
    run = await run_bounded_speech_work(
        settings,
        partial(
            AssistantSpeechService(SqlAssistantSpeechRepository(db), store, settings).run,
            account_id=auth.account_id,
            assistant_generation_run_id=run_id,
            provider=provider,
        ),
    )
    return assistant_speech_response(db, run)


@router.get(
    "/v1/assistant-speeches/{run_id}",
    response_model=AssistantSpeechRunResponse,
)
async def get_assistant_speech(
    run_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> AssistantSpeechRunResponse:
    run = db.get(AssistantSpeechRun, run_id)
    if run is None or run.account_id != auth.account_id:
        raise AuthorizationError("assistant speech run was not found")
    return assistant_speech_response(db, run)


@router.get("/v1/assistant-speeches/{run_id}/audio")
async def get_assistant_speech_audio(
    run_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    store: AudioObjectStore = Depends(get_audio_store),
) -> Response:
    run = db.get(AssistantSpeechRun, run_id)
    if (
        run is None
        or run.account_id != auth.account_id
        or run.status != "succeeded"
        or run.audio_asset_id is None
    ):
        raise AuthorizationError("assistant speech was not found")
    asset = db.get(AudioAsset, run.audio_asset_id)
    if asset is None or asset.account_id != auth.account_id:
        raise AuthorizationError("assistant speech audio was not found")
    return Response(
        content=store.read(asset.storage_key),
        media_type=asset.mime_type,
        headers={"Cache-Control": "private, max-age=31536000, immutable"},
    )


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
    if settings.environment != "test":
        start_acoustic_warmup(
            db,
            store,
            settings,
            account_id=auth.account_id,
            utterance_id=utterance_id,
        )
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
    "/v1/perceptions/{run_id}/speech-analysis",
    response_model=PerceivedSpeechAnalysisResponse,
)
async def analyze_perceived_speech(
    run_id: uuid.UUID,
    body: PerceivedAnalysisCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_request_settings),
    store: AudioObjectStore = Depends(get_audio_store),
) -> PerceivedSpeechAnalysisResponse:
    service = PerceivedSpeechAnalysisService(db, store, settings)
    run = await run_bounded_analysis_work(
        settings,
        partial(
            service.run,
            account_id=auth.account_id,
            perception_run_id=run_id,
        ),
    )
    return analysis_response(run)


@router.get("/v1/perceptions/{run_id}/readings", response_model=PerceivedReadingResponse)
async def get_perceived_readings(
    run_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> PerceivedReadingResponse:
    """Deterministic text-only projection; never waits for audio analysis or meaning."""
    run = db.get(PerceptionRun, run_id)
    if run is None or run.account_id != auth.account_id:
        raise AuthorizationError("perception run was not found")
    return reading_response(run)


@router.get(
    "/v1/perceived-speech-analyses/{analysis_id}", response_model=PerceivedSpeechAnalysisResponse
)
async def get_perceived_speech_analysis(
    analysis_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> PerceivedSpeechAnalysisResponse:
    run = db.get(PerceivedSpeechAnalysis, analysis_id)
    if run is None or run.account_id != auth.account_id:
        raise AuthorizationError("speech analysis was not found")
    return analysis_response(run)


@router.post("/v1/utterances/{utterance_id}/acoustics", response_model=AcousticRunResponse)
async def analyze_utterance_acoustics(
    utterance_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_request_settings),
    store: AudioObjectStore = Depends(get_audio_store),
) -> AcousticRunResponse:
    """Target-independent raw evidence, never a pronunciation or tone assessment."""
    analyzer = build_acoustic_analyzer(settings)
    run = await run_bounded_analysis_work(
        settings,
        partial(
            AcousticAnalysisService(db, store, analyzer).run,
            account_id=auth.account_id,
            utterance_id=utterance_id,
        ),
    )
    return acoustic_response(run)


@router.post(
    "/v1/perceptions/{run_id}/contextual-interpretations",
    response_model=ContextualInterpretationRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_contextual_interpretation(
    run_id: uuid.UUID,
    body: ContextualInterpretationCreate,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_request_settings),
    interpreter: ContextualInterpretationPort = Depends(get_contextual_interpreter),
) -> ContextualInterpretationRunResponse:
    service = ContextualInterpretationService(SqlContextualInterpretationRepository(db))
    run = await run_bounded_speech_work(
        settings,
        partial(
            service.run,
            account_id=auth.account_id,
            perception_run_id=run_id,
            context_snapshot=body.context_snapshot,
            interpreter=interpreter,
        ),
    )
    return contextual_interpretation_response(run)


@router.get(
    "/v1/contextual-interpretations/{run_id}",
    response_model=ContextualInterpretationRunResponse,
)
async def get_contextual_interpretation(
    run_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ContextualInterpretationRunResponse:
    run = db.get(ContextualInterpretationRun, run_id)
    if run is None or run.account_id != auth.account_id:
        raise AuthorizationError("contextual interpretation run was not found")
    return contextual_interpretation_response(run)


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
        if run is None or run.account_id != auth.account_id or run.utterance_id != utterance_id:
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


@router.get("/v1/pronunciation-targets/{target_id}", response_model=PronunciationTargetResponse)
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


@router.get("/v1/pronunciation-attempts/{attempt_id}", response_model=PronunciationAttemptResponse)
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
    return await run_bounded_analysis_work(
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

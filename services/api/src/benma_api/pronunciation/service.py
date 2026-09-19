"""Known-target assessment orchestration and immutable target snapshots."""

from __future__ import annotations

import logging
import os
import subprocess
import time
import uuid
from collections.abc import Callable

from sqlalchemy.orm import Session

from benma_api.db.models import (
    AssessmentRun,
    AudioAsset,
    PronunciationAttempt,
    PronunciationTarget,
    Utterance,
)
from benma_api.errors import AuthorizationError, BenmaError, ProviderUnavailableError
from benma_api.speech.contracts import KnownTargetAssessmentInput, PronunciationAssessmentPort
from benma_api.speech.raw_evidence import encode_raw_payload
from benma_api.storage.audio_store import AudioObjectStore

logger = logging.getLogger(__name__)


def log_assessment(run: AssessmentRun) -> None:
    logger.info(
        "assessment evidence appended",
        extra={
            "account_id": run.account_id,
            "run_id": run.id,
            "provider": run.provider,
            "status": run.status,
            "latency_ms": run.latency_ms,
        },
    )


def current_git_commit() -> str:
    configured = os.environ.get("BENMA_GIT_COMMIT_SHA")
    if configured:
        return configured[:64]
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return "undocumented"
    value = completed.stdout.strip()
    return value[:64] if value else "undocumented"


def target_snapshot(target: PronunciationTarget) -> dict[str, object]:
    return {
        "id": str(target.id),
        "text": target.text,
        "display_pinyin": target.display_pinyin,
        "pinyin_syllables": target.pinyin_syllables,
        "lexical_tones": target.lexical_tones,
        "target_source": target.target_source,
        "pinyin_source": target.pinyin_source,
        "syllable_units": target.syllable_units,
        "surface_tone_expectation": target.surface_tone_expectation,
        "parent_target_id": str(target.parent_target_id) if target.parent_target_id else None,
    }


class AssessmentService:
    def __init__(
        self, db: Session, store: AudioObjectStore, provider: PronunciationAssessmentPort
    ) -> None:
        self.db = db
        self.store = store
        self.provider = provider

    def run(
        self, *, account_id: uuid.UUID, attempt_id: uuid.UUID, timeout_seconds: float
    ) -> AssessmentRun:
        run, error = self.prepare(
            account_id=account_id, attempt_id=attempt_id, timeout_seconds=timeout_seconds
        )()
        self.db.add(run)
        self.db.commit()
        log_assessment(run)
        if error is not None:
            raise error
        return run

    def prepare(
        self, *, account_id: uuid.UUID, attempt_id: uuid.UUID, timeout_seconds: float
    ) -> Callable[[], tuple[AssessmentRun, BenmaError | None]]:
        attempt = self.db.get(PronunciationAttempt, attempt_id)
        if attempt is None or attempt.account_id != account_id:
            raise AuthorizationError("pronunciation attempt was not found")
        target = self.db.get(PronunciationTarget, attempt.target_id)
        utterance = self.db.get(Utterance, attempt.utterance_id)
        if (
            target is None
            or target.account_id != account_id
            or utterance is None
            or utterance.account_id != account_id
        ):
            raise AuthorizationError("attempt evidence was not found")
        asset = self.db.get(AudioAsset, utterance.canonical_audio_asset_id)
        if asset is None or asset.account_id != account_id:
            raise AuthorizationError("attempt audio was not found")
        snapshot = target_snapshot(target)
        request = KnownTargetAssessmentInput(
            attempt_id=attempt_id,
            canonical_audio=self.store.read(asset.storage_key),
            mime_type=asset.mime_type,
            target_snapshot=snapshot,
            timeout_seconds=timeout_seconds,
        )
        audio_sha256 = asset.sha256
        sample_rate_hz = asset.sample_rate_hz

        provider = self.provider

        def compute() -> tuple[AssessmentRun, BenmaError | None]:
            started = time.perf_counter()
            try:
                response = provider.assess(request)
                raw = encode_raw_payload(response.raw_payload)
                normalized = response.evidence.normalized()
            except Exception as caught:
                exc = (
                    caught
                    if isinstance(caught, BenmaError)
                    else ProviderUnavailableError("Assessment unavailable")
                )
                run = AssessmentRun(
                    account_id=account_id,
                    pronunciation_attempt_id=attempt_id,
                    provider=provider.provider_name,
                    product=provider.product_name,
                    adapter_version=provider.adapter_version,
                    target_snapshot=snapshot,
                    git_commit_sha=current_git_commit(),
                    audio_sha256=audio_sha256,
                    sample_rate_hz=sample_rate_hz,
                    request_configuration={},
                    transport_timings_ms={},
                    normalized_result=None,
                    status="failed",
                    error_code=exc.code,
                    error_message=exc.message,
                    latency_ms=round((time.perf_counter() - started) * 1000),
                )
                return run, exc
            run = AssessmentRun(
                account_id=account_id,
                pronunciation_attempt_id=attempt_id,
                provider=provider.provider_name,
                product=provider.product_name,
                provider_version=response.provider_version,
                adapter_version=provider.adapter_version,
                target_snapshot=snapshot,
                git_commit_sha=current_git_commit(),
                audio_sha256=audio_sha256,
                sample_rate_hz=sample_rate_hz,
                request_configuration=response.request_configuration or {},
                transport_timings_ms=response.transport_timings_ms or {},
                normalized_result=normalized,
                raw_payload_json=raw.json_value,
                raw_payload_text=raw.text_value,
                raw_payload_sha256=raw.sha256,
                latency_ms=round((time.perf_counter() - started) * 1000),
                status="succeeded",
            )
            return run, None

        return compute

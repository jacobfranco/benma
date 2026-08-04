"""Known-target assessment orchestration and immutable target snapshots."""

from __future__ import annotations

import logging
import time
import uuid

from sqlalchemy.orm import Session

from benma_api.db.models import (
    AssessmentRun,
    AudioAsset,
    PronunciationAttempt,
    PronunciationTarget,
    Utterance,
)
from benma_api.errors import AuthorizationError, BenmaError
from benma_api.speech.contracts import KnownTargetAssessmentInput, PronunciationAssessmentPort
from benma_api.speech.raw_evidence import encode_raw_payload
from benma_api.storage.audio_store import AudioObjectStore

logger = logging.getLogger(__name__)


def target_snapshot(target: PronunciationTarget) -> dict[str, object]:
    return {
        "id": str(target.id),
        "text": target.text,
        "display_pinyin": target.display_pinyin,
        "pinyin_syllables": target.pinyin_syllables,
        "lexical_tones": target.lexical_tones,
        "target_source": target.target_source,
        "pinyin_source": target.pinyin_source,
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
        started = time.perf_counter()
        try:
            response = self.provider.assess(request)
        except BenmaError as exc:
            run = AssessmentRun(
                account_id=account_id,
                pronunciation_attempt_id=attempt_id,
                provider=self.provider.provider_name,
                product=self.provider.product_name,
                adapter_version=self.provider.adapter_version,
                target_snapshot=snapshot,
                normalized_result=None,
                status="failed",
                error_code=exc.code,
                error_message=exc.message,
                latency_ms=round((time.perf_counter() - started) * 1000),
            )
            self.db.add(run)
            self.db.commit()
            logger.info(
                "assessment evidence appended",
                extra={
                    "account_id": account_id,
                    "utterance_id": utterance.id,
                    "run_id": run.id,
                    "provider": self.provider.provider_name,
                    "status": "failed",
                },
            )
            raise
        raw = encode_raw_payload(response.raw_payload)
        run = AssessmentRun(
            account_id=account_id,
            pronunciation_attempt_id=attempt_id,
            provider=self.provider.provider_name,
            product=self.provider.product_name,
            provider_version=response.provider_version,
            adapter_version=self.provider.adapter_version,
            target_snapshot=snapshot,
            normalized_result=response.evidence.normalized(),
            raw_payload_json=raw.json_value,
            raw_payload_text=raw.text_value,
            raw_payload_sha256=raw.sha256,
            latency_ms=round((time.perf_counter() - started) * 1000),
            status="succeeded",
        )
        self.db.add(run)
        self.db.commit()
        logger.info(
            "assessment evidence appended",
            extra={
                "account_id": account_id,
                "utterance_id": utterance.id,
                "run_id": run.id,
                "provider": self.provider.provider_name,
                "status": "succeeded",
            },
        )
        return run

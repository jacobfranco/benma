"""Unknown-target orchestration: canonical audio in, append-only evidence out."""

from __future__ import annotations

import logging
import time
import uuid

from benma_api.db.models import PerceptionRun
from benma_api.errors import AuthorizationError, BenmaError
from benma_api.perception.repository import PerceptionRepository
from benma_api.speech.contracts import PerceptionPort, UnknownTargetPerceptionInput
from benma_api.speech.raw_evidence import encode_raw_payload
from benma_api.storage.audio_store import AudioObjectStore

logger = logging.getLogger(__name__)


class PerceptionService:
    def __init__(
        self,
        repository: PerceptionRepository,
        store: AudioObjectStore,
        provider: PerceptionPort,
    ) -> None:
        self.repository = repository
        self.store = store
        self.provider = provider

    def run(
        self,
        *,
        account_id: uuid.UUID,
        utterance_id: uuid.UUID,
        language_hint: str,
        timeout_seconds: float,
    ) -> PerceptionRun:
        asset = self.repository.load_canonical_asset(account_id, utterance_id)
        if asset is None:
            raise AuthorizationError("utterance was not found")
        request = UnknownTargetPerceptionInput(
            utterance_id=utterance_id,
            canonical_audio=self.store.read(asset.storage_key),
            mime_type=asset.mime_type,
            language_hint=language_hint,
            timeout_seconds=timeout_seconds,
        )
        started = time.perf_counter()
        try:
            response = self.provider.perceive(request)
        except BenmaError as exc:
            run = PerceptionRun(
                account_id=account_id,
                utterance_id=utterance_id,
                provider=self.provider.provider_name,
                product=self.provider.product_name,
                adapter_version=self.provider.adapter_version,
                normalized_result=None,
                status="failed",
                error_code=exc.code,
                error_message=exc.message,
                latency_ms=round((time.perf_counter() - started) * 1000),
            )
            self.repository.append_run(run)
            logger.info(
                "perception evidence appended",
                extra={
                    "account_id": account_id,
                    "utterance_id": utterance_id,
                    "run_id": run.id,
                    "provider": self.provider.provider_name,
                    "status": "failed",
                },
            )
            raise
        raw = encode_raw_payload(response.raw_payload)
        evidence = response.evidence
        run = PerceptionRun(
            account_id=account_id,
            utterance_id=utterance_id,
            provider=self.provider.provider_name,
            product=self.provider.product_name,
            provider_version=response.provider_version,
            adapter_version=self.provider.adapter_version,
            transcript=evidence.transcript,
            alternatives=evidence.alternatives,
            provider_uncertainty=evidence.provider_uncertainty,
            normalized_result=evidence.normalized(),
            raw_payload_json=raw.json_value,
            raw_payload_text=raw.text_value,
            raw_payload_sha256=raw.sha256,
            latency_ms=round((time.perf_counter() - started) * 1000),
            status="succeeded",
        )
        self.repository.append_run(run)
        logger.info(
            "perception evidence appended",
            extra={
                "account_id": account_id,
                "utterance_id": utterance_id,
                "run_id": run.id,
                "provider": self.provider.provider_name,
                "status": "succeeded",
            },
        )
        return run

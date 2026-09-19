"""Bounded optional acoustic work started alongside ASR, with worker-owned sessions.

No job broker or polling state: a lost warmup is harmless because final analysis
uses the same persisted, single-flight acoustic service. Perception never joins it.
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from benma_api.config import Settings
from benma_api.db.models import Utterance
from benma_api.errors import AuthorizationError
from benma_api.pronunciation.acoustics import AcousticAnalysisService, build_acoustic_analyzer
from benma_api.storage.audio_store import AudioObjectStore

WORKERS = ThreadPoolExecutor(max_workers=2, thread_name_prefix="acoustic-warmup")
CAPACITY = threading.BoundedSemaphore(2)
GUARD = threading.RLock()
IN_FLIGHT: dict[tuple[int, uuid.UUID, uuid.UUID, str], Future[uuid.UUID | None]] = {}
LOGGER = logging.getLogger(__name__)


def start_acoustic_warmup(
    db: Session,
    store: AudioObjectStore,
    settings: Settings,
    *,
    account_id: uuid.UUID,
    utterance_id: uuid.UUID,
) -> Future[uuid.UUID | None] | None:
    if (
        db.scalar(
            select(Utterance.id).where(
                Utterance.id == utterance_id,
                Utterance.account_id == account_id,
            )
        )
        is None
    ):
        raise AuthorizationError("utterance was not found")
    bind = db.get_bind()
    if settings.acoustic_provider == "disabled" or not isinstance(bind, Engine):
        return None
    try:
        analyzer = build_acoustic_analyzer(settings)
    except Exception:
        LOGGER.info("optional acoustic warmup initialization unavailable")
        return None
    config = json.dumps(
        [analyzer.algorithm_name, analyzer.algorithm_version, analyzer.parameters], sort_keys=True
    )
    key = (id(bind), account_id, utterance_id, config)

    def work() -> uuid.UUID | None:
        try:
            with Session(bind, expire_on_commit=False) as worker_db:
                run = AcousticAnalysisService(worker_db, store, analyzer).run(
                    account_id=account_id,
                    utterance_id=utterance_id,
                )
                return run.id
        except Exception:
            # No provider message, transcript, path, credentials, or URL in this log.
            LOGGER.info("optional acoustic warmup unavailable")
            return None

    def finished(_future: Future[uuid.UUID | None]) -> None:
        with GUARD:
            IN_FLIGHT.pop(key, None)
            CAPACITY.release()

    with GUARD:
        if key in IN_FLIGHT:
            return IN_FLIGHT[key]
        if not CAPACITY.acquire(blocking=False):
            return None
        try:
            future = WORKERS.submit(work)
        except RuntimeError:
            CAPACITY.release()
            return None
        IN_FLIGHT[key] = future
        future.add_done_callback(finished)
        return future

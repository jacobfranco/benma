"""Guard legacy target endpoints using persisted perception, never target text."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from benma_api.audio.presence import require_speech
from benma_api.db.models import PerceptionRun
from benma_api.errors import NoSpeechError


def require_saved_speech(
    db: Session, canonical: bytes, *, account_id: uuid.UUID, utterance_id: uuid.UUID
) -> None:
    perception = db.scalar(
        select(PerceptionRun)
        .where(PerceptionRun.account_id == account_id, PerceptionRun.utterance_id == utterance_id)
        .order_by(PerceptionRun.created_at.desc(), PerceptionRun.id.desc())
        .limit(1)
    )
    if perception is not None and perception.error_code == "no_speech":
        raise NoSpeechError("Didn't catch any speech. Try again.")
    require_speech(canonical, transcript=perception.transcript if perception is not None else None)

"""Narrow repository boundary that cannot query targets or corrections."""

from __future__ import annotations

import uuid
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from benma_api.db.models import AudioAsset, PerceptionRun, Utterance


class PerceptionRepository(Protocol):
    def load_canonical_asset(
        self, account_id: uuid.UUID, utterance_id: uuid.UUID
    ) -> AudioAsset | None: ...
    def append_run(self, run: PerceptionRun) -> None: ...


class SqlPerceptionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def load_canonical_asset(
        self, account_id: uuid.UUID, utterance_id: uuid.UUID
    ) -> AudioAsset | None:
        return self.db.scalar(
            select(AudioAsset)
            .join(Utterance, Utterance.canonical_audio_asset_id == AudioAsset.id)
            .where(Utterance.id == utterance_id, Utterance.account_id == account_id)
        )

    def append_run(self, run: PerceptionRun) -> None:
        self.db.add(run)
        self.db.commit()

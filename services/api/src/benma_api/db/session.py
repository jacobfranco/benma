"""Database engine, request sessions, and evidence immutability guard."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from benma_api.config import get_settings
from benma_api.db.models import APPEND_ONLY_MODELS

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _session_factory


async def get_db() -> AsyncGenerator[Session, None]:
    with get_session_factory()() as session:
        yield session


@event.listens_for(Session, "before_flush")
def prevent_evidence_mutation(session: Session, *_: object) -> None:
    protected = APPEND_ONLY_MODELS
    if any(isinstance(item, protected) for item in session.dirty):
        raise ValueError("evidence records are append-only")
    if any(isinstance(item, protected) for item in session.deleted):
        raise ValueError("evidence records are append-only")

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from benma_api.config import get_settings


def test_migrations_upgrade_empty_database_and_downgrade(
    tmp_path: Path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "migration.db"
    monkeypatch.setenv("BENMA_ENVIRONMENT", "test")
    monkeypatch.setenv("BENMA_DATABASE_URL", f"sqlite:///{database}")
    get_settings.cache_clear()
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{database}")
    assert {
        "accounts",
        "audio_assets",
        "utterances",
        "perception_runs",
        "assessment_runs",
        "user_corrections",
    }.issubset(inspect(engine).get_table_names())
    command.check(config)
    command.downgrade(config, "base")
    assert inspect(engine).get_table_names() == ["alembic_version"]
    engine.dispose()
    get_settings.cache_clear()

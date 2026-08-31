from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from benma_api.config import get_settings


def test_migrations_upgrade_empty_database_and_downgrade(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "migration.db"
    monkeypatch.setenv("BENMA_ENVIRONMENT", "test")
    monkeypatch.setenv("BENMA_DATABASE_URL", f"sqlite:///{database}")
    get_settings.cache_clear()
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{database}")
    inspector = inspect(engine)
    assert {
        "accounts",
        "audio_assets",
        "utterances",
        "perception_runs",
        "contextual_interpretation_runs",
        "assessment_runs",
        "user_corrections",
    }.issubset(inspector.get_table_names())
    contextual_columns = {
        column["name"]: column for column in inspector.get_columns("contextual_interpretation_runs")
    }
    assert contextual_columns["inferred_text"]["nullable"] is True
    assert contextual_columns["decision"]["nullable"] is False
    assert any(
        str(constraint["name"]).endswith("ck_contextual_interpretation_decision")
        for constraint in inspector.get_check_constraints("contextual_interpretation_runs")
    )
    command.check(config)
    command.downgrade(config, "base")
    assert inspect(engine).get_table_names() == ["alembic_version"]
    engine.dispose()
    get_settings.cache_clear()


def test_contextual_decision_migration_backfills_existing_runs(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "migration-backfill.db"
    monkeypatch.setenv("BENMA_ENVIRONMENT", "test")
    monkeypatch.setenv("BENMA_DATABASE_URL", f"sqlite:///{database}")
    get_settings.cache_clear()
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    command.upgrade(config, "0005")
    engine = create_engine(f"sqlite:///{database}")
    insert = text(
        "INSERT INTO contextual_interpretation_runs "
        "(id, account_id, perception_run_id, interpreter, interpreter_version, "
        "interpreter_configuration, context_snapshot, inferred_text, uncertainty, "
        "clarification_needed, created_at) "
        "VALUES (:id, :account_id, :perception_run_id, 'fixture', '1', '{}', '{}', "
        ":inferred_text, '{}', :clarification_needed, CURRENT_TIMESTAMP)"
    )
    with engine.begin() as connection:
        for row_id, inferred_text, clarification_needed in (
            ("1" * 32, None, False),
            ("2" * 32, "我想买水果。", False),
            ("3" * 32, None, True),
        ):
            connection.execute(
                insert,
                {
                    "id": row_id,
                    "account_id": "a" * 32,
                    "perception_run_id": "b" * 32,
                    "inferred_text": inferred_text,
                    "clarification_needed": clarification_needed,
                },
            )

    command.upgrade(config, "head")

    with engine.connect() as connection:
        decisions = dict(
            connection.execute(
                text("SELECT id, decision FROM contextual_interpretation_runs")
            ).all()
        )
    assert decisions == {
        "1" * 32: "preserve",
        "2" * 32: "infer",
        "3" * 32: "clarify",
    }
    engine.dispose()
    get_settings.cache_clear()

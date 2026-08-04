from __future__ import annotations

from benchmark.fixtures import materialize_replay_fixtures
from benchmark.models import ProviderRun
from benchmark.providers.status import provider_status_scorecard
from benchmark.storage import load_model


def test_fixture_runs_do_not_promote_provider_lifecycle(tmp_path) -> None:  # type: ignore[no-untyped-def]
    materialize_replay_fixtures(tmp_path)
    runs = [load_model(path, ProviderRun) for path in (tmp_path / "runs").glob("*.json")]
    rows = provider_status_scorecard(runs)
    assert rows
    assert all(row["observed_live_run_count"] == 0 for row in rows)
    assert all(row["lifecycle"] not in {"live_validated", "calibrated"} for row in rows)
    assert all(row["calibration_scope"] == "none" for row in rows)

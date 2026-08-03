from __future__ import annotations

from pathlib import Path

import pytest

from benchmark.evaluation.cost import calculate_scenarios, load_catalog

ROOT = Path(__file__).resolve().parents[1]


def test_cost_scenarios_include_required_scales() -> None:
    catalog = load_catalog(ROOT / "benchmark/evaluation/cost/pricing-v2026-08-03.json")
    result = calculate_scenarios(catalog)
    assert set(result) == {
        "10_minutes_per_day",
        "30_minutes_per_day",
        "60_minutes_per_day",
        "100_users_30_minutes_per_day",
        "1000_users_30_minutes_per_day",
    }


def test_google_monthly_cost_uses_dated_rate() -> None:
    catalog = load_catalog(ROOT / "benchmark/evaluation/cost/pricing-v2026-08-03.json")
    scenario = calculate_scenarios(catalog)["10_minutes_per_day"]
    assert isinstance(scenario, dict)
    products = scenario["products"]
    google = next(item for item in products if item["provider"] == "google_cloud")
    assert google["monthly_cost_usd"] == pytest.approx(300 * 0.016)


def test_unknown_token_price_stays_unknown() -> None:
    catalog = load_catalog(ROOT / "benchmark/evaluation/cost/pricing-v2026-08-03.json")
    scenario = calculate_scenarios(catalog)["30_minutes_per_day"]
    products = scenario["products"]
    gpt = next(item for item in products if item["product"] == "gpt-4o-transcribe")
    assert gpt["monthly_cost_usd"] is None


def test_realtime_whisper_uses_documented_duration_rate() -> None:
    catalog = load_catalog(ROOT / "benchmark/evaluation/cost/pricing-v2026-08-03.json")
    scenario = calculate_scenarios(catalog)["10_minutes_per_day"]
    products = scenario["products"]
    realtime = next(item for item in products if item["product"] == "gpt-realtime-whisper")
    assert realtime["monthly_cost_usd"] == pytest.approx(300 * 0.017)

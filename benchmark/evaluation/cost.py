"""Versioned, configuration-driven provider cost scenarios."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PriceAssumption(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: str
    product: str
    category: Literal["asr", "pronunciation", "tts", "llm"]
    billing_unit: Literal["audio_minute", "request", "million_input_tokens", "unknown"]
    unit_price_usd: float | None = Field(default=None, ge=0)
    assumed_requests_per_minute: float = Field(default=1.0, gt=0)
    evidence_status: Literal["documented", "converted", "estimate", "unknown"]
    source_url: str
    accessed_date: str
    notes: str

    def cost_for_usage(self, *, minutes: float, attempts: float) -> float | None:
        if self.unit_price_usd is None:
            return None
        if self.billing_unit == "audio_minute":
            return minutes * self.unit_price_usd
        if self.billing_unit == "request":
            return attempts * self.unit_price_usd
        return None


class PricingCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0.0"] = "1.0.0"
    pricing_date: str
    assumptions: tuple[PriceAssumption, ...]


SCENARIOS: dict[str, dict[str, float]] = {
    "one_attempt": {"minutes": 1 / 6, "attempts": 1},
    "100_attempts": {"minutes": 100 / 6, "attempts": 100},
    "10_minutes_per_day": {"minutes": 10 * 30, "attempts": 10 * 30 * 6},
    "30_minutes_per_day": {"minutes": 30 * 30, "attempts": 30 * 30 * 6},
    "60_minutes_per_day": {"minutes": 60 * 30, "attempts": 60 * 30 * 6},
    "100_users_30_minutes_per_day": {
        "minutes": 100 * 30 * 30,
        "attempts": 100 * 30 * 30 * 6,
    },
    "1000_users_30_minutes_per_day": {
        "minutes": 1000 * 30 * 30,
        "attempts": 1000 * 30 * 30 * 6,
    },
}


def load_catalog(path: Path) -> PricingCatalog:
    return PricingCatalog.model_validate_json(path.read_text(encoding="utf-8"))


def calculate_scenarios(catalog: PricingCatalog) -> dict[str, object]:
    output: dict[str, object] = {}
    for scenario, usage in SCENARIOS.items():
        minutes = usage["minutes"]
        attempts = usage["attempts"]
        products: list[dict[str, object]] = []
        totals: dict[str, float] = defaultdict(float)
        unknown_categories: set[str] = set()
        for assumption in catalog.assumptions:
            cost = assumption.cost_for_usage(minutes=minutes, attempts=attempts)
            products.append(
                {
                    "provider": assumption.provider,
                    "product": assumption.product,
                    "category": assumption.category,
                    "monthly_cost_usd": cost,
                    "estimated_cost_usd": cost,
                    "evidence_status": assumption.evidence_status,
                }
            )
            if cost is None:
                unknown_categories.add(assumption.category)
            else:
                totals[assumption.category] += cost
        output[scenario] = {
            "practice_minutes_per_month": minutes,
            "attempt_count": attempts,
            "products": products,
            "category_totals_usd_if_all_products_used": dict(totals),
            "categories_with_unknown_cost": sorted(unknown_categories),
            "pronunciation_architectures": _pronunciation_architectures(products),
        }
    return output


def _pronunciation_architectures(
    products: list[dict[str, object]],
) -> dict[str, object]:
    pronunciation = [item for item in products if item["category"] == "pronunciation"]
    singles = {
        str(item["provider"]): item["estimated_cost_usd"] for item in pronunciation
    }
    pairs: dict[str, float | None] = {}
    for index, left in enumerate(pronunciation):
        for right in pronunciation[index + 1 :]:
            left_cost = left["estimated_cost_usd"]
            right_cost = right["estimated_cost_usd"]
            key = f"{left['provider']}+{right['provider']}"
            pairs[key] = (
                float(left_cost) + float(right_cost)
                if isinstance(left_cost, int | float)
                and isinstance(right_cost, int | float)
                else None
            )
    costs = [item["estimated_cost_usd"] for item in pronunciation]
    numeric_costs = [float(value) for value in costs if isinstance(value, int | float)]
    benchmark_all = (
        sum(numeric_costs)
        if costs and len(numeric_costs) == len(costs)
        else None
    )
    return {
        "single_provider": singles,
        "two_provider_ensemble": pairs,
        "benchmark_all_providers": benchmark_all,
        "warning": (
            "Benchmark multi-provider calls are not a production recommendation. "
            "Unknown vendor prices keep ensemble totals unknown."
        ),
    }

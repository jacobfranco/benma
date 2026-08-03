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

    def cost_for_minutes(self, minutes: float) -> float | None:
        if self.unit_price_usd is None:
            return None
        if self.billing_unit == "audio_minute":
            return minutes * self.unit_price_usd
        if self.billing_unit == "request":
            return minutes * self.assumed_requests_per_minute * self.unit_price_usd
        return None


class PricingCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0.0"] = "1.0.0"
    pricing_date: str
    assumptions: tuple[PriceAssumption, ...]


SCENARIOS = {
    "10_minutes_per_day": 10 * 30,
    "30_minutes_per_day": 30 * 30,
    "60_minutes_per_day": 60 * 30,
    "100_users_30_minutes_per_day": 100 * 30 * 30,
    "1000_users_30_minutes_per_day": 1000 * 30 * 30,
}


def load_catalog(path: Path) -> PricingCatalog:
    return PricingCatalog.model_validate_json(path.read_text(encoding="utf-8"))


def calculate_scenarios(catalog: PricingCatalog) -> dict[str, object]:
    output: dict[str, object] = {}
    for scenario, minutes in SCENARIOS.items():
        products: list[dict[str, object]] = []
        totals: dict[str, float] = defaultdict(float)
        unknown_categories: set[str] = set()
        for assumption in catalog.assumptions:
            cost = assumption.cost_for_minutes(minutes)
            products.append(
                {
                    "provider": assumption.provider,
                    "product": assumption.product,
                    "category": assumption.category,
                    "monthly_cost_usd": cost,
                    "evidence_status": assumption.evidence_status,
                }
            )
            if cost is None:
                unknown_categories.add(assumption.category)
            else:
                totals[assumption.category] += cost
        output[scenario] = {
            "practice_minutes_per_month": minutes,
            "products": products,
            "category_totals_usd_if_all_products_used": dict(totals),
            "categories_with_unknown_cost": sorted(unknown_categories),
        }
    return output

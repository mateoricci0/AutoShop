"""Builds rich context dicts from ProductCandidate for LLM prompt templates."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class ProductContext:
    """Normalized product info ready for template rendering."""
    title: str
    description: str | None
    category: str | None
    features: list[str]
    price: str | None
    price_range: str | None
    target_audience: str | None
    source: str
    images: list[str]
    raw_data: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "features": self.features,
            "price": self.price,
            "price_range": self.price_range,
            "target_audience": self.target_audience,
            "source": self.source,
            "images": self.images,
        }


def build_product_context(candidate: Any) -> ProductContext:
    """Convert a ProductCandidate ORM instance to a ProductContext."""
    raw = candidate.raw_data or {}
    ai = candidate.ai_analysis or {}

    features: list[str] = (
        raw.get("features")
        or raw.get("specifications")
        or []
    )
    if isinstance(features, str):
        features = [f.strip() for f in features.split(",") if f.strip()]

    price: str | None = None
    if candidate.recommended_price:
        price = f"${candidate.recommended_price:.2f}"

    price_range: str | None = None
    if candidate.cost and candidate.recommended_price:
        price_range = f"${candidate.cost:.2f} – ${candidate.recommended_price:.2f}"

    target_audience = (
        raw.get("target_audience")
        or ai.get("target_audience")
        or _infer_audience(candidate)
    )

    images: list[str] = []
    if isinstance(candidate.images, list):
        images = [img if isinstance(img, str) else img.get("url", "") for img in candidate.images]

    return ProductContext(
        title=candidate.title,
        description=candidate.description,
        category=candidate.category,
        features=features[:8],
        price=price,
        price_range=price_range,
        target_audience=target_audience,
        source=candidate.source,
        images=images[:5],
        raw_data=raw,
    )


def _infer_audience(candidate: Any) -> str:
    """Heuristic audience inference from category and title."""
    title_lower = (candidate.title or "").lower()
    cat = (candidate.category or "").lower()

    if any(w in title_lower or w in cat for w in ("baby", "kid", "children", "toddler")):
        return "parents with young children"
    if any(w in title_lower or w in cat for w in ("gym", "fitness", "sport", "workout")):
        return "fitness enthusiasts"
    if any(w in title_lower or w in cat for w in ("pet", "dog", "cat")):
        return "pet owners"
    if any(w in title_lower or w in cat for w in ("kitchen", "cooking", "chef")):
        return "home cooks"
    if any(w in title_lower or w in cat for w in ("beauty", "skincare", "hair")):
        return "beauty-conscious consumers"
    return "general online shoppers"

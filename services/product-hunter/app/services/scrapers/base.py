from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import hashlib


@dataclass
class ScrapedProduct:
    title: str
    source: str  # must match source enum values in DB
    source_url: str | None = None
    source_product_id: str | None = None
    description: str | None = None
    cost: float | None = None        # purchase/wholesale cost
    retail_price: float | None = None
    images: list[dict] = field(default_factory=list)  # [{url, alt}]
    category: str | None = None
    tags: list[str] = field(default_factory=list)
    # Engagement signals (used in scoring)
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    shares: int | None = None
    saves: int | None = None
    rating: float | None = None
    reviews_count: int | None = None
    sales_count: int | None = None
    # Extra metadata passed to AI
    raw_data: dict = field(default_factory=dict)
    scraped_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def compute_hash(self) -> str:
        """SHA-256 dedup key: source + product_id (or title fallback)."""
        unique_part = self.source_product_id or self.title.lower().strip()
        key = f"{self.source}:{unique_part}"
        return hashlib.sha256(key.encode()).hexdigest()

    def to_engagement_summary(self) -> str:
        parts = []
        if self.views:         parts.append(f"{self.views:,} views")
        if self.likes:         parts.append(f"{self.likes:,} likes")
        if self.comments:      parts.append(f"{self.comments:,} comments")
        if self.shares:        parts.append(f"{self.shares:,} shares")
        if self.saves:         parts.append(f"{self.saves:,} saves")
        if self.rating:        parts.append(f"{self.rating}/5 rating")
        if self.reviews_count: parts.append(f"{self.reviews_count:,} reviews")
        if self.sales_count:   parts.append(f"{self.sales_count:,} sales")
        return ", ".join(parts) if parts else "no engagement data"


class ScraperUnavailable(Exception):
    """Raised when a scraper cannot run due to missing credentials or connectivity."""
    pass


class BaseScraper(ABC):
    name: str  # must match source enum in DB schema
    requires_playwright: bool = False
    requires_api_key: bool = False

    @abstractmethod
    async def scrape(self, limit: int = 20) -> list[ScrapedProduct]:
        """Scrape products. Raise ScraperUnavailable if cannot run."""
        ...

    async def is_available(self) -> bool:
        """Quick check if scraper can run (credentials present, etc.)."""
        return True

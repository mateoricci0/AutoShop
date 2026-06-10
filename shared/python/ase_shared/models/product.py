"""Product ORM models — ProductCandidate and ProductPublished."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Enum,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ase_shared.database.base import Base, TimestampMixin


class ProductStatus(str, enum.Enum):
    """Matches the ``product_status`` PostgreSQL enum exactly."""

    pending = "pending"
    analyzing = "analyzing"
    approved = "approved"
    rejected = "rejected"
    publishing = "publishing"
    published = "published"
    archived = "archived"


_product_status_type = Enum(
    ProductStatus,
    name="product_status",
    create_type=False,  # type already created by schema migration
)


class ProductCandidate(Base, TimestampMixin):
    """A product discovered by the scraping agents, awaiting AI analysis."""

    __tablename__ = "products_candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Identification
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_product_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_hash: Mapped[str | None] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
    )

    # Pricing
    cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    recommended_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    estimated_margin: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    # AI scores (0.00 - 100.00)
    demand_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    competition_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    trend_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    engagement_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    saturation_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    branding_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    margin_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    success_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Metadata
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        server_default="{}",
    )
    images: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    ai_analysis: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)

    # State
    status: Mapped[ProductStatus] = mapped_column(
        _product_status_type,
        nullable=False,
        server_default="pending",
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scraped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProductPublished(Base, TimestampMixin):
    """A product that has been (or is being) published to a Shopify store."""

    __tablename__ = "products_published"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    store_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Shopify identifiers
    shopify_product_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True
    )
    shopify_variant_ids: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default="{}"
    )
    shopify_collection_ids: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default="{}"
    )
    shopify_handle: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Product content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default="{}"
    )

    # Pricing
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    compare_at_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    cost_per_item: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # SEO
    seo_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Variants & images (Shopify JSON structures)
    variants: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    options: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    images: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")

    # State
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="draft"
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

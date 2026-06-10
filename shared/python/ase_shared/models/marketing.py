"""Marketing ORM models — MarketingAsset and GeneratedImage."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ase_shared.database.base import Base, TimestampMixin


class AssetStatus(str, enum.Enum):
    """Matches the ``asset_status`` PostgreSQL enum exactly."""

    draft = "draft"
    generating = "generating"
    approved = "approved"
    active = "active"
    archived = "archived"


class ImageType(str, enum.Enum):
    """Matches the ``image_type`` PostgreSQL enum exactly."""

    hero = "hero"
    lifestyle = "lifestyle"
    infographic = "infographic"
    before_after = "before_after"
    banner = "banner"
    ad_square = "ad_square"
    ad_story = "ad_story"


_asset_status_type = Enum(
    AssetStatus,
    name="asset_status",
    create_type=False,
)

_image_type_type = Enum(
    ImageType,
    name="image_type",
    create_type=False,
)


class MarketingAsset(Base, TimestampMixin):
    """AI-generated marketing copy and ad content for a product candidate."""

    __tablename__ = "marketing_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    store_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Branding
    brand_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tagline: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Content
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    long_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    bullet_points: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    faqs: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")

    # SEO
    meta_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default="{}"
    )

    # Copy variants
    hooks: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    headlines: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    ctas: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    ad_copies: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")

    # Platform-specific ads
    facebook_ads: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    instagram_ads: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    tiktok_ads: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    google_ads: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    email_campaigns: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")

    # Generation metadata
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    generation_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)

    status: Mapped[AssetStatus] = mapped_column(
        _asset_status_type,
        nullable=False,
        server_default="draft",
    )


class GeneratedImage(Base, TimestampMixin):
    """An AI-generated image for a product candidate."""

    __tablename__ = "generated_images"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    store_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    type: Mapped[ImageType] = mapped_column(_image_type_type, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    negative_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Storage
    storage_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Image metadata
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    format: Mapped[str | None] = mapped_column(String(20), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Generation metadata
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    generation_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    generation_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clip_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)

    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="pending"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

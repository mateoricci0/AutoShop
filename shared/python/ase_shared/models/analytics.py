"""Analytics ORM models — Analytics and Campaign."""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ase_shared.database.base import Base, TimestampMixin


class AnalyticsDecision(str, enum.Enum):
    """Matches the ``analytics_decision`` PostgreSQL enum exactly."""

    scale = "scale"
    optimize = "optimize"
    pause = "pause"
    insufficient_data = "insufficient_data"


_analytics_decision_type = Enum(
    AnalyticsDecision,
    name="analytics_decision",
    create_type=False,
)


class Campaign(Base, TimestampMixin):
    """An ad campaign linked to a store and optionally a published product."""

    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    store_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    marketing_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    platform: Mapped[str] = mapped_column(String(100), nullable=False)
    campaign_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    external_campaign_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    external_adset_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    budget_daily: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    budget_lifetime: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="USD"
    )

    targeting: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="draft"
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class Analytics(Base):
    """Aggregated analytics data row for a store/campaign/product combination."""

    __tablename__ = "analytics"
    __table_args__ = (
        UniqueConstraint(
            "store_id",
            "campaign_id",
            "product_id",
            "date",
            "hour",
            "platform",
            "granularity",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    store_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    date: Mapped[date] = mapped_column(Date, nullable=False)
    hour: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    granularity: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="daily"
    )
    platform: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Traffic
    impressions: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    clicks: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    reach: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    # Conversions
    add_to_carts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    checkouts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    orders: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    refunds: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")

    # Calculated KPIs
    ctr: Mapped[Decimal | None] = mapped_column(Numeric(8, 6), nullable=True)
    cpc: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    cpa: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    cpm: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    roas: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    conversion_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 6), nullable=True)
    aov: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    profit: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    auto_decision: Mapped[AnalyticsDecision | None] = mapped_column(
        _analytics_decision_type, nullable=True
    )
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

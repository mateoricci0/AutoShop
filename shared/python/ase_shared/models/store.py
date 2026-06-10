"""Store ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ase_shared.database.base import Base, TimestampMixin


class Store(Base, TimestampMixin):
    """A Shopify store managed by ASE.

    ``shopify_access_token`` is ALWAYS Fernet-encrypted before being written
    to this column — never stored in plaintext, never returned in API responses.
    """

    __tablename__ = "stores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    shopify_domain: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    shopify_access_token: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Fernet-encrypted Shopify Admin API token",
    )
    shopify_store_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    shopify_plan: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        server_default="USD",
    )
    timezone: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        server_default="UTC",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    settings: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
    )

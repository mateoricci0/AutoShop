"""Notification ORM model."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ase_shared.database.base import Base


class NotificationEvent(str, enum.Enum):
    """Matches the ``notification_event`` PostgreSQL enum exactly."""

    new_winner = "new_winner"
    critical_error = "critical_error"
    product_published = "product_published"
    roas_drop = "roas_drop"
    roas_scale = "roas_scale"
    agent_error = "agent_error"
    store_connected = "store_connected"
    weekly_report = "weekly_report"


_notification_event_type = Enum(
    NotificationEvent,
    name="notification_event",
    create_type=False,
)


class Notification(Base):
    """A notification dispatched to one or more channels (email, Discord, etc.)."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    store_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_type: Mapped[NotificationEvent] = mapped_column(
        _notification_event_type, nullable=False
    )
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="info"
    )

    channels: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default="{}"
    )
    delivery_status: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default="{}"
    )

    reference_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

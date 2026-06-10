"""Auth ORM model — AdminSession."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ase_shared.database.base import Base


class AdminSession(Base):
    """Single-admin session stored in PostgreSQL for persistence / audit.

    The *source of truth* for active sessions is Redis (fast TTL-based lookup).
    This table is kept for audit/cleanup purposes.
    ``token_hash`` stores SHA-256 of the raw opaque token — NOT bcrypt, so
    lookups stay O(1) constant-time.
    """

    __tablename__ = "admin_session"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

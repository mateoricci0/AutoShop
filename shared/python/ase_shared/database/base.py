"""SQLAlchemy 2.0 declarative base and shared mixins."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Single declarative base for all ASE ORM models.

    Every model file must import this class so Alembic can detect all
    table definitions via ``ase_shared.models``.
    """


class TimestampMixin:
    """Adds ``created_at`` / ``updated_at`` columns to a model.

    ``updated_at`` is kept current by both the SQLAlchemy ORM
    (via ``onupdate``) and the PostgreSQL trigger defined in the schema.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

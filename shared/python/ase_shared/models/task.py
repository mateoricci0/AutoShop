"""Task ORM models — Task and ScheduledJob."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ase_shared.database.base import Base, TimestampMixin


class TaskStatus(str, enum.Enum):
    """Matches the ``task_status`` PostgreSQL enum exactly."""

    pending = "pending"
    started = "started"
    success = "success"
    failure = "failure"
    revoked = "revoked"
    retry = "retry"


class ScheduleFrequency(str, enum.Enum):
    """Matches the ``schedule_frequency`` PostgreSQL enum exactly."""

    hourly = "hourly"
    every_6h = "every_6h"
    every_12h = "every_12h"
    daily = "daily"
    weekly = "weekly"


_task_status_type = Enum(
    TaskStatus,
    name="task_status",
    create_type=False,
)

_schedule_frequency_type = Enum(
    ScheduleFrequency,
    name="schedule_frequency",
    create_type=False,
)


class Task(Base, TimestampMixin):
    """Tracks the lifecycle of a Celery task for observability and retry logic."""

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    celery_task_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    task_queue: Mapped[str] = mapped_column(
        String(100), nullable=False, server_default="default"
    )
    store_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    parent_task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    kwargs: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[TaskStatus] = mapped_column(
        _task_status_type,
        nullable=False,
        server_default="pending",
    )

    eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, server_default="3")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="5")


class ScheduledJob(Base, TimestampMixin):
    """Defines a recurring scheduled task (cron-style) managed by the ASE scheduler."""

    __tablename__ = "scheduled_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    store_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    task_kwargs: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")

    frequency: Mapped[ScheduleFrequency] = mapped_column(
        _schedule_frequency_type, nullable=False
    )
    cron_expression: Mapped[str | None] = mapped_column(String(100), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    run_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

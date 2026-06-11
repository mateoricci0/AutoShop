"""Notification schemas — aliased to match frontend field names."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class NotificationOut(BaseModel):
    id: str
    type: str = Field(alias="event_type")
    title: str
    message: str = Field(alias="body")
    read: bool = Field(alias="is_read")
    data: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class DispatchRequest(BaseModel):
    notification_id: str
    channels: list[str] | None = None

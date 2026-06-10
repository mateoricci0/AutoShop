"""Pydantic schemas for store endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StoreCreate(BaseModel):
    """Request body for creating a store."""

    name: str = Field(min_length=1, max_length=255)
    shopify_domain: str = Field(
        pattern=r"^[a-zA-Z0-9-]+\.myshopify\.com$",
        description="Must be in the format <handle>.myshopify.com",
    )
    shopify_access_token: str = Field(min_length=1)
    currency: str = "USD"
    timezone: str = "UTC"


class StoreUpdate(BaseModel):
    """Request body for updating a store (partial)."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    settings: dict | None = None


class StoreResponse(BaseModel):
    """Serialised store returned by the API.

    ``shopify_access_token`` is intentionally excluded — it is never returned.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    shopify_domain: str
    shopify_store_id: str | None
    shopify_plan: str | None
    currency: str
    timezone: str
    is_active: bool
    last_synced_at: datetime | None
    settings: dict
    created_at: datetime
    updated_at: datetime


class TestConnectionResponse(BaseModel):
    """Result of calling Shopify's shop.json endpoint."""

    ok: bool
    shopify_plan: str
    currency: str
    shop_name: str

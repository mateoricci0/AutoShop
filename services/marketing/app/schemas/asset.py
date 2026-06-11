"""Pydantic schemas for marketing assets."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class AssetListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID | None
    store_id: uuid.UUID | None
    brand_name: str | None
    tagline: str | None
    short_description: str | None
    status: str
    ai_model: str | None
    generation_cost: Decimal | None
    tokens_used: int | None
    created_at: datetime
    updated_at: datetime


class AssetDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID | None
    store_id: uuid.UUID | None

    brand_name: str | None
    tagline: str | None
    short_description: str | None
    long_description: str | None
    bullet_points: list[Any]
    faqs: list[Any]

    meta_title: str | None
    meta_description: str | None
    keywords: list[str]

    hooks: list[Any]
    headlines: list[Any]
    ctas: list[Any]
    ad_copies: list[Any]

    facebook_ads: dict[str, Any]
    instagram_ads: dict[str, Any]
    tiktok_ads: dict[str, Any]
    google_ads: dict[str, Any]
    email_campaigns: dict[str, Any]

    ai_model: str | None
    generation_cost: Decimal | None
    tokens_used: int | None
    status: str

    created_at: datetime
    updated_at: datetime


class AssetUpdateRequest(BaseModel):
    brand_name: str | None = None
    tagline: str | None = None
    short_description: str | None = None
    long_description: str | None = None
    bullet_points: list[Any] | None = None
    faqs: list[Any] | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    keywords: list[str] | None = None
    hooks: list[Any] | None = None
    headlines: list[Any] | None = None
    ctas: list[Any] | None = None
    ad_copies: list[Any] | None = None
    facebook_ads: dict[str, Any] | None = None
    instagram_ads: dict[str, Any] | None = None
    tiktok_ads: dict[str, Any] | None = None
    google_ads: dict[str, Any] | None = None
    email_campaigns: dict[str, Any] | None = None
    status: str | None = None


class GenerateRequest(BaseModel):
    candidate_id: uuid.UUID
    store_id: uuid.UUID | None = None
    provider: str | None = None  # override default provider

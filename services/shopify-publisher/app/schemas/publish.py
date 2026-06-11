"""Pydantic schemas for the Shopify Publisher service."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PublishRequest(BaseModel):
    candidate_id: UUID
    store_id: UUID
    price: Decimal = Field(..., gt=0, description="Sale price in store currency")
    compare_at_price: Decimal | None = None
    vendor: str | None = None
    product_type: str | None = None
    publish_status: str = "active"


class ChecklistItem(BaseModel):
    key: str
    label: str
    passed: bool
    detail: str | None = None


class ChecklistResult(BaseModel):
    candidate_id: str
    store_id: str
    passed: bool
    items: list[ChecklistItem]


class PublishedProductListItem(BaseModel):
    id: str
    candidate_id: str | None
    store_id: str
    shopify_product_id: str | None
    shopify_handle: str | None
    title: str
    price: str
    compare_at_price: str | None
    status: str
    published_at: datetime | None
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PublishedProductDetail(PublishedProductListItem):
    description_html: str | None
    vendor: str | None
    product_type: str | None
    tags: list[str]
    seo_title: str | None
    seo_description: str | None
    shopify_variant_ids: list[str]
    shopify_collection_ids: list[str]
    variants: list[Any]
    options: list[Any]
    images: list[Any]

    class Config:
        from_attributes = True


class TriggerPublishResponse(BaseModel):
    job_id: str
    status: str
    candidate_id: str
    store_id: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    step: str | None = None
    result: dict | None = None
    error: str | None = None


class ArchiveRequest(BaseModel):
    reason: str | None = None

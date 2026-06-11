"""Pydantic schemas for generated images."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ImageListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID | None
    store_id: uuid.UUID | None
    type: str
    storage_url: str | None
    thumbnail_url: str | None
    width: int | None
    height: int | None
    format: str | None
    model: str | None
    provider: str | None
    clip_score: Decimal | None
    status: str
    created_at: datetime


class ImageDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID | None
    store_id: uuid.UUID | None
    type: str
    prompt: str
    negative_prompt: str | None
    storage_key: str | None
    storage_url: str | None
    thumbnail_url: str | None
    width: int | None
    height: int | None
    format: str | None
    file_size_bytes: int | None
    model: str | None
    provider: str | None
    generation_cost: Decimal | None
    generation_time_ms: int | None
    clip_score: Decimal | None
    status: str
    error_message: str | None
    retry_count: int
    created_at: datetime
    updated_at: datetime


class GenerateImagesRequest(BaseModel):
    candidate_id: uuid.UUID
    store_id: uuid.UUID | None = None
    image_types: list[str] | None = None  # None = all 7 types
    provider: str | None = None           # "openai" | "stability" | None = auto


class RegenerateImageRequest(BaseModel):
    image_id: uuid.UUID
    provider: str | None = None

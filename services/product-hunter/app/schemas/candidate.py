from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Any


class CandidateListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    source: str
    source_url: str | None
    cost: float | None
    recommended_price: float | None
    estimated_margin: float | None
    success_score: float | None
    demand_score: float | None
    trend_score: float | None
    engagement_score: float | None
    status: str
    category: str | None
    tags: list[str]
    images: list[dict]
    created_at: datetime


class CandidateDetail(CandidateListItem):
    description: str | None
    competition_score: float | None
    saturation_score: float | None
    branding_score: float | None
    margin_score: float | None
    raw_data: dict
    ai_analysis: dict
    ai_model: str | None
    ai_tokens_used: int | None
    ai_cost: float | None
    rejection_reason: str | None
    approved_at: datetime | None
    scraped_at: datetime | None
    analyzed_at: datetime | None
    updated_at: datetime


class ApproveRequest(BaseModel):
    store_id: UUID | None = None


class RejectRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class HuntJobRequest(BaseModel):
    store_id: UUID | None = None
    sources: list[str] | None = None  # None = all enabled sources
    force: bool = False  # skip dedup check


class CandidateFilters(BaseModel):
    status: str | None = None
    source: str | None = None
    min_score: float | None = None
    max_score: float | None = None
    store_id: UUID | None = None

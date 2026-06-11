"""Pydantic schemas — match the frontend analytics types exactly."""
from __future__ import annotations

from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    total_revenue: float
    total_cost: float
    total_profit: float
    total_orders: int
    overall_roas: float
    total_impressions: int
    total_clicks: int
    active_campaigns: int


class TimeSeriesPoint(BaseModel):
    date: str
    value: float


class ProductAnalytics(BaseModel):
    product_id: str
    product_title: str
    revenue: float
    cost: float
    profit: float
    orders: int
    roas: float
    impressions: int
    clicks: int
    decision: str
    period_start: str
    period_end: str


class AgentStatus(BaseModel):
    id: str
    name: str
    display_name: str
    description: str
    status: str
    last_run_at: str | None
    last_error: str | None
    service_url: str


class AgentLog(BaseModel):
    id: str
    agent_name: str
    level: str
    message: str
    ai_cost: float | None
    tokens_used: int | None
    duration_ms: int | None
    created_at: str


class ScheduledJobItem(BaseModel):
    id: str
    name: str
    description: str | None
    task_name: str
    frequency: str
    is_active: bool
    last_run_at: str | None
    last_run_status: str | None
    next_run_at: str | None
    run_count: int
    failure_count: int

    class Config:
        from_attributes = True


class UpdateJobRequest(BaseModel):
    frequency: str | None = None
    is_active: bool | None = None


class CollectRequest(BaseModel):
    store_id: str
    days: int = 7

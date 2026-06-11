"""Analytics summary, timeseries and per-product endpoints."""
from __future__ import annotations

import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ase_shared.models.analytics import Analytics
from ase_shared.models.product import ProductPublished

from ..dependencies import get_db
from ..schemas.analytics import AnalyticsSummary, TimeSeriesPoint, ProductAnalytics
from ..services.decision_engine import make_decision

router = APIRouter(prefix="/summary", tags=["analytics"])


def _parse_range(range_str: str) -> date:
    days = {"7d": 7, "30d": 30, "90d": 90}.get(range_str, 30)
    return date.today() - timedelta(days=days)


@router.get("", response_model=AnalyticsSummary)
async def get_summary(
    store_id: str,
    range: str = "30d",
    db: AsyncSession = Depends(get_db),
):
    since = _parse_range(range)
    sid = uuid.UUID(store_id)

    result = await db.execute(
        select(
            func.coalesce(func.sum(Analytics.revenue), 0).label("total_revenue"),
            func.coalesce(func.sum(Analytics.cost), 0).label("total_cost"),
            func.coalesce(func.sum(Analytics.profit), 0).label("total_profit"),
            func.coalesce(func.sum(Analytics.orders), 0).label("total_orders"),
            func.coalesce(func.sum(Analytics.impressions), 0).label("total_impressions"),
            func.coalesce(func.sum(Analytics.clicks), 0).label("total_clicks"),
        ).where(
            Analytics.store_id == sid,
            Analytics.date >= since,
        )
    )
    row = result.one()

    total_revenue = float(row.total_revenue or 0)
    total_cost = float(row.total_cost or 0)
    roas = total_revenue / total_cost if total_cost > 0 else 0.0

    # Count active campaigns (distinct campaign_ids in range)
    camp_result = await db.execute(
        select(func.count(Analytics.campaign_id.distinct())).where(
            Analytics.store_id == sid,
            Analytics.date >= since,
            Analytics.campaign_id.isnot(None),
        )
    )
    active_campaigns = camp_result.scalar_one() or 0

    return AnalyticsSummary(
        total_revenue=total_revenue,
        total_cost=total_cost,
        total_profit=float(row.total_profit or 0),
        total_orders=int(row.total_orders or 0),
        overall_roas=round(roas, 4),
        total_impressions=int(row.total_impressions or 0),
        total_clicks=int(row.total_clicks or 0),
        active_campaigns=active_campaigns,
    )


router_ts = APIRouter(prefix="/timeseries", tags=["analytics"])


@router_ts.get("", response_model=list[TimeSeriesPoint])
async def get_timeseries(
    store_id: str,
    metric: str = "revenue",
    range: str = "30d",
    db: AsyncSession = Depends(get_db),
):
    since = _parse_range(range)
    sid = uuid.UUID(store_id)

    metric_col = {
        "revenue": Analytics.revenue,
        "cost": Analytics.cost,
        "profit": Analytics.profit,
        "orders": Analytics.orders,
        "impressions": Analytics.impressions,
        "clicks": Analytics.clicks,
    }.get(metric, Analytics.revenue)

    result = await db.execute(
        select(
            Analytics.date,
            func.sum(metric_col).label("value"),
        ).where(
            Analytics.store_id == sid,
            Analytics.date >= since,
        ).group_by(Analytics.date).order_by(Analytics.date)
    )
    return [
        TimeSeriesPoint(date=str(r.date), value=float(r.value or 0))
        for r in result.all()
    ]


router_products = APIRouter(prefix="/products", tags=["analytics"])


@router_products.get("", response_model=list[ProductAnalytics])
async def get_product_analytics(
    store_id: str,
    range: str = "30d",
    db: AsyncSession = Depends(get_db),
):
    since = _parse_range(range)
    sid = uuid.UUID(store_id)

    result = await db.execute(
        select(
            Analytics.product_id,
            func.sum(Analytics.revenue).label("revenue"),
            func.sum(Analytics.cost).label("cost"),
            func.sum(Analytics.profit).label("profit"),
            func.sum(Analytics.orders).label("orders"),
            func.sum(Analytics.impressions).label("impressions"),
            func.sum(Analytics.clicks).label("clicks"),
        ).where(
            Analytics.store_id == sid,
            Analytics.date >= since,
            Analytics.product_id.isnot(None),
        ).group_by(Analytics.product_id)
    )
    rows = result.all()

    items = []
    for row in rows:
        revenue = float(row.revenue or 0)
        cost = float(row.cost or 0)
        orders = int(row.orders or 0)
        roas = revenue / cost if cost > 0 else 0.0
        decision = make_decision(roas if cost > 0 else None, orders)

        # Fetch product title
        pub = await db.get(ProductPublished, row.product_id)
        title = pub.title if pub else str(row.product_id)[:8]

        items.append(ProductAnalytics(
            product_id=str(row.product_id),
            product_title=title,
            revenue=revenue,
            cost=cost,
            profit=float(row.profit or 0),
            orders=orders,
            roas=round(roas, 4),
            impressions=int(row.impressions or 0),
            clicks=int(row.clicks or 0),
            decision=decision,
            period_start=str(since),
            period_end=str(date.today()),
        ))

    return sorted(items, key=lambda x: x.revenue, reverse=True)

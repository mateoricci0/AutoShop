"""Shopify Orders collector — fetches orders from the Admin API and upserts analytics rows."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import httpx
import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ase_shared.models.analytics import Analytics
from ase_shared.models.product import ProductPublished
from ase_shared.models.store import Store
from ase_shared.security.encryption import decrypt

from .kpi_calculator import calculate_kpis

logger = structlog.get_logger()

_API_VERSION = "2024-10"


async def collect_store_analytics(
    db: AsyncSession,
    store: Store,
    days: int = 7,
    api_version: str = _API_VERSION,
) -> dict:
    """Fetch Shopify orders for the last `days` days and upsert analytics rows."""
    access_token = decrypt(store.shopify_access_token)
    domain = store.shopify_domain

    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    url = f"https://{domain}/admin/api/{api_version}/orders.json"
    params = {
        "status": "any",
        "created_at_min": since,
        "limit": 250,
        "fields": "id,created_at,total_price,subtotal_price,total_discounts,line_items,financial_status,refunds",
    }

    headers = {"X-Shopify-Access-Token": access_token}
    orders = []

    async with httpx.AsyncClient(timeout=30) as client:
        while url:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            orders.extend(data.get("orders", []))
            link = resp.headers.get("Link", "")
            url = None
            params = {}
            for part in link.split(","):
                if 'rel="next"' in part:
                    url = part.split(";")[0].strip().strip("<>")
                    break

    # Aggregate by date × product (via line_item title)
    # We store a single "store-level" row per day (no campaign granularity for now)
    daily: dict[str, dict] = {}

    for order in orders:
        if order.get("financial_status") not in ("paid", "partially_paid"):
            continue
        order_date = order["created_at"][:10]
        if order_date not in daily:
            daily[order_date] = {
                "revenue": Decimal("0"),
                "orders": 0,
                "refunds": Decimal("0"),
            }
        daily[order_date]["revenue"] += Decimal(str(order.get("total_price") or 0))
        daily[order_date]["orders"] += 1
        for refund in order.get("refunds", []):
            for rt in refund.get("refund_line_items", []):
                daily[order_date]["refunds"] += Decimal(str(rt.get("subtotal") or 0))

    inserted = 0
    for day_str, agg in daily.items():
        day_date = date.fromisoformat(day_str)
        kpis = calculate_kpis({"revenue": agg["revenue"], "cost": 0, "orders": agg["orders"], "refunds": agg["refunds"]})

        # Upsert: try insert, ignore conflict
        existing = await db.execute(
            select(Analytics).where(
                Analytics.store_id == store.id,
                Analytics.campaign_id == None,
                Analytics.product_id == None,
                Analytics.date == day_date,
                Analytics.granularity == "daily",
                Analytics.platform == "shopify",
            ).limit(1)
        )
        row = existing.scalar_one_or_none()
        if row is None:
            row = Analytics(
                store_id=store.id,
                date=day_date,
                granularity="daily",
                platform="shopify",
            )
            db.add(row)

        row.revenue = agg["revenue"]
        row.orders = agg["orders"]
        row.refunds = agg["refunds"]
        row.profit = Decimal(str(kpis["profit"] or 0))
        inserted += 1

    await db.commit()
    logger.info("analytics_collected", store_id=str(store.id), days=days, rows=inserted)
    return {"store_id": str(store.id), "days": days, "rows_upserted": inserted}

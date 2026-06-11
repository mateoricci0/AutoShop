"""KPI calculator — derives ROAS, CTR, CPC, CPA, CVR, AOV, profit from raw rows."""
from __future__ import annotations

from decimal import Decimal
from typing import Any


def calculate_kpis(row: dict[str, Any]) -> dict[str, Any | None]:
    revenue = Decimal(str(row.get("revenue") or 0))
    cost = Decimal(str(row.get("cost") or 0))
    impressions = int(row.get("impressions") or 0)
    clicks = int(row.get("clicks") or 0)
    orders = int(row.get("orders") or 0)
    refunds = Decimal(str(row.get("refunds") or 0))

    roas = float(revenue / cost) if cost > 0 else None
    ctr = float(clicks / impressions) if impressions > 0 else None
    cpc = float(cost / clicks) if clicks > 0 else None
    cpa = float(cost / orders) if orders > 0 else None
    cvr = float(orders / clicks) if clicks > 0 else None
    aov = float((revenue - refunds) / orders) if orders > 0 else None
    profit = float(revenue - cost - refunds)

    return {
        "roas": roas,
        "ctr": ctr,
        "cpc": cpc,
        "cpa": cpa,
        "conversion_rate": cvr,
        "aov": aov,
        "profit": profit,
    }

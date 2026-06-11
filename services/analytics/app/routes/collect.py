"""Manual analytics collection trigger."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ase_shared.models.store import Store

from ..dependencies import get_db
from ..schemas.analytics import CollectRequest
from ..tasks.analytics_tasks import collect_analytics

router = APIRouter(prefix="/collect", tags=["collect"])


@router.post("")
async def trigger_collect(
    body: CollectRequest,
    db: AsyncSession = Depends(get_db),
):
    if body.store_id:
        result = await db.execute(
            select(Store).where(Store.id == body.store_id, Store.is_active == True)
        )
        stores = result.scalars().all()
    else:
        result = await db.execute(select(Store).where(Store.is_active == True))
        stores = result.scalars().all()

    job_ids = []
    for store in stores:
        task = collect_analytics.delay(str(store.id), body.days or 7)
        job_ids.append(task.id)

    return {"queued": len(job_ids), "job_ids": job_ids}

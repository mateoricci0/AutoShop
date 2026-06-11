"""Celery tasks for analytics collection."""
from __future__ import annotations

import asyncio
import structlog
from celery import Celery
from sqlalchemy import select

from ase_shared.db import AsyncSessionLocal
from ase_shared.models.store import Store

from ..config import settings
from ..services.shopify_collector import collect_store_analytics

logger = structlog.get_logger()

celery_app = Celery(
    "analytics",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]


@celery_app.task(
    name="analytics.collect_analytics",
    queue="analytics.collect",
    bind=True,
    max_retries=2,
)
def collect_analytics(self, store_id: str, days: int = 7):
    async def _run():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Store).where(Store.id == store_id, Store.is_active == True)
            )
            store = result.scalar_one_or_none()
            if not store:
                logger.warning("analytics_collect_skip", store_id=store_id, reason="not_found")
                return {"error": "store_not_found"}
            return await collect_store_analytics(db, store, days=days)

    try:
        return asyncio.get_event_loop().run_until_complete(_run())
    except Exception as exc:
        logger.error("analytics_collect_error", store_id=store_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))

"""Celery tasks for Shopify publishing."""
from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal

import structlog

from .celery_app import celery_app

logger = structlog.get_logger()


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="publish.shopify",
    queue="publish.shopify",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def publish_to_shopify(
    self,
    candidate_id: str,
    store_id: str,
    price: str,
    compare_at_price: str | None = None,
    vendor: str | None = None,
    product_type: str | None = None,
    publish_status: str = "active",
):
    return run_async(
        _publish_async(
            self,
            candidate_id,
            store_id,
            price,
            compare_at_price,
            vendor,
            product_type,
            publish_status,
        )
    )


async def _publish_async(
    task,
    candidate_id: str,
    store_id: str,
    price: str,
    compare_at_price: str | None,
    vendor: str | None,
    product_type: str | None,
    publish_status: str,
):
    from ase_shared.database.session import AsyncSessionLocal
    from ..config import settings
    from ..services.publisher import publish_to_shopify as do_publish

    def update_step(step: str):
        task.update_state(state="STARTED", meta={"step": step})

    async with AsyncSessionLocal() as db:
        try:
            published = await do_publish(
                db=db,
                candidate_id=uuid.UUID(candidate_id),
                store_id=uuid.UUID(store_id),
                price=Decimal(price),
                compare_at_price=Decimal(compare_at_price) if compare_at_price else None,
                vendor=vendor,
                product_type=product_type,
                publish_status=publish_status,
                api_version=settings.SHOPIFY_API_VERSION,
                update_step=update_step,
            )
            return {
                "published_id": str(published.id),
                "shopify_product_id": published.shopify_product_id,
                "shopify_handle": published.shopify_handle,
                "candidate_id": candidate_id,
            }
        except Exception as e:
            logger.error("publish_task_failed", candidate_id=candidate_id, error=str(e))
            raise task.retry(exc=e)

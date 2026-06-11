"""Celery task to dispatch a notification through configured channels."""
from __future__ import annotations

import asyncio
import uuid
import structlog

from ase_shared.db import AsyncSessionLocal
from ase_shared.models.notification import Notification

from .celery_app import celery_app
from ..services.dispatcher import dispatch

logger = structlog.get_logger()


@celery_app.task(
    name="notifications.dispatch",
    queue="notifications.dispatch",
    bind=True,
    max_retries=2,
)
def dispatch_notification(self, notification_id: str, channels: list[str] | None = None):
    async def _run():
        async with AsyncSessionLocal() as db:
            notif = await db.get(Notification, uuid.UUID(notification_id))
            if not notif:
                logger.warning("notification_not_found", notification_id=notification_id)
                return {"error": "not_found"}

            results = await dispatch(
                title=notif.title,
                body=notif.body or "",
                channels=channels,
            )

            notif.delivery_status = results
            notif.channels = list(results.keys())
            await db.commit()
            logger.info("notification_dispatched", notification_id=notification_id, results=results)
            return results

    try:
        return asyncio.get_event_loop().run_until_complete(_run())
    except Exception as exc:
        logger.error("notification_dispatch_error", notification_id=notification_id, error=str(exc))
        raise self.retry(exc=exc, countdown=30 * (self.request.retries + 1))

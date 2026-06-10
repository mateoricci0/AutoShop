"""Stub tasks for the Scheduler service."""

from __future__ import annotations

import structlog

from .celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(name="scheduler.tasks.cleanup_old_tasks")
def cleanup_old_tasks() -> dict[str, str]:
    """Remove completed/failed Celery task results older than 24 hours."""
    logger.info("cleanup_old_tasks.started")
    # Stub: full implementation will query the result backend and purge expired entries
    logger.info("cleanup_old_tasks.complete")
    return {"status": "ok"}

"""Celery Beat application for the ASE Scheduler service.

Defines periodic tasks that drive the product lifecycle:
- Product hunting runs every 6 hours
- Analytics collection runs every 6 hours
- Daily cleanup tasks
"""

from __future__ import annotations

from celery.schedules import crontab

from ase_shared.messaging.celery_config import make_celery

celery_app = make_celery("scheduler")

celery_app.conf.beat_schedule = {
    # ── Product lifecycle ──────────────────────────────────────────────────
    "hunt-products": {
        "task": "product_hunter.tasks.hunt_products",
        "schedule": crontab(minute="0", hour="*/6"),  # every 6 hours
    },
    "collect-analytics": {
        "task": "analytics.tasks.collect_analytics",
        "schedule": crontab(minute="30", hour="*/6"),  # every 6 hours, offset by 30m
    },
    # ── Daily maintenance ──────────────────────────────────────────────────
    "cleanup-expired-sessions": {
        "task": "auth.tasks.cleanup_sessions",
        "schedule": crontab(hour="2", minute="0"),  # daily at 02:00 UTC
    },
    "cleanup-old-tasks": {
        "task": "scheduler.tasks.cleanup_old_tasks",
        "schedule": crontab(hour="3", minute="0"),  # daily at 03:00 UTC
    },
}

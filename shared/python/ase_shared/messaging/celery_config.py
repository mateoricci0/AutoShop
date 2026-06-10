"""Celery application factory for ASE services.

Each service calls ``make_celery(name)`` to get a configured Celery app that
connects to Redis as both broker and result backend.
"""

from __future__ import annotations

import os

from celery import Celery

# ---------------------------------------------------------------------------
# Queue definitions — all valid queue names in the system
# ---------------------------------------------------------------------------
QUEUES = [
    "products.scrape",
    "products.analyze",
    "marketing.generate",
    "images.generate",
    "publish.shopify",
    "analytics.collect",
    "notifications.send",
    "auth.tasks",
    "scheduler.tasks",
]

_REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")


def make_celery(service_name: str) -> Celery:
    """Return a Celery application pre-configured for ASE.

    Args:
        service_name: Human-readable label used for logging/tracing.

    Returns:
        A :class:`celery.Celery` instance ready to use.
    """
    app = Celery(service_name)

    app.conf.update(
        broker_url=_REDIS_URL,
        result_backend=_REDIS_URL,
        # Serialisation
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        # Timezone
        timezone="UTC",
        enable_utc=True,
        # Results
        result_expires=3600,  # 1 hour
        # Routing
        task_default_queue="default",
        task_routes={
            "*.scrape.*": {"queue": "products.scrape"},
            "*.analyze.*": {"queue": "products.analyze"},
            "*.marketing.*": {"queue": "marketing.generate"},
            "*.images.*": {"queue": "images.generate"},
            "*.publish.*": {"queue": "publish.shopify"},
            "*.analytics.*": {"queue": "analytics.collect"},
            "*.notifications.*": {"queue": "notifications.send"},
        },
        # Worker behaviour
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        task_track_started=True,
        task_reject_on_worker_lost=True,
        # Retry policy defaults
        task_soft_time_limit=300,   # 5 min soft
        task_time_limit=600,        # 10 min hard
    )

    return app

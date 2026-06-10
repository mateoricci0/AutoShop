"""Celery application for the Analytics service."""

from ase_shared.messaging.celery_config import make_celery

celery_app = make_celery("analytics")

"""Celery application for the Product Hunter service."""

from ase_shared.messaging.celery_config import make_celery

celery_app = make_celery("product-hunter")

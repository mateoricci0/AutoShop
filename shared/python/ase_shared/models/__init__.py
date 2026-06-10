"""Import all ORM models so Alembic can detect table definitions via Base.metadata."""

from ase_shared.models.auth import AdminSession
from ase_shared.models.store import Store
from ase_shared.models.product import ProductCandidate, ProductPublished, ProductStatus
from ase_shared.models.marketing import (
    AssetStatus,
    GeneratedImage,
    ImageType,
    MarketingAsset,
)
from ase_shared.models.analytics import Analytics, AnalyticsDecision, Campaign
from ase_shared.models.task import ScheduledJob, ScheduleFrequency, Task, TaskStatus
from ase_shared.models.notification import Notification, NotificationEvent
from ase_shared.models.settings import Settings

__all__ = [
    "AdminSession",
    "Analytics",
    "AnalyticsDecision",
    "AssetStatus",
    "Campaign",
    "GeneratedImage",
    "ImageType",
    "MarketingAsset",
    "Notification",
    "NotificationEvent",
    "ProductCandidate",
    "ProductPublished",
    "ProductStatus",
    "ScheduledJob",
    "ScheduleFrequency",
    "Settings",
    "Store",
    "Task",
    "TaskStatus",
]

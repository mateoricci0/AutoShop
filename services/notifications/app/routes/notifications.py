"""Notification CRUD — list, mark-read, mark-all-read, config status."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ase_shared.models.notification import Notification, NotificationEvent

from ..config import settings
from ..dependencies import get_db
from ..schemas.notification import NotificationOut
from ..tasks.notification_tasks import dispatch_notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
async def list_notifications(
    store_id: str | None = None,
    unread_only: bool = False,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    q = select(Notification).order_by(Notification.created_at.desc()).limit(limit)
    if store_id:
        q = q.where(Notification.store_id == uuid.UUID(store_id))
    if unread_only:
        q = q.where(Notification.is_read == False)

    result = await db.execute(q)
    return result.scalars().all()


@router.patch("/{notification_id}/read", response_model=NotificationOut)
async def mark_read(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
):
    nid = uuid.UUID(notification_id)
    notif = await db.get(Notification, nid)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.is_read = True
    notif.read_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(notif)
    return notif


@router.post("/mark-all-read")
async def mark_all_read(
    store_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        update(Notification)
        .where(Notification.is_read == False)
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    if store_id:
        stmt = stmt.where(Notification.store_id == uuid.UUID(store_id))

    result = await db.execute(stmt)
    await db.commit()
    return {"updated": result.rowcount}


@router.get("/config")
async def get_config():
    """Return which notification channels are configured."""
    return {
        "discord": bool(settings.DISCORD_WEBHOOK),
        "telegram": bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID),
        "slack": bool(settings.SLACK_WEBHOOK),
        "email": bool(settings.SMTP_HOST and settings.SMTP_USER),
    }


@router.post("/test")
async def send_test(db: AsyncSession = Depends(get_db)):
    """Create a test notification and dispatch it through all configured channels."""
    notif = Notification(
        title="Test de Notificación ASE",
        body="Si ves este mensaje, las notificaciones están funcionando correctamente.",
        event_type=NotificationEvent.agent_error,
        severity="info",
        channels=[],
        delivery_status={},
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)

    dispatch_notification.delay(str(notif.id))
    return {"queued": True, "notification_id": str(notif.id)}

"""Dispatch a notification through all configured channels (3 retries each)."""
from __future__ import annotations

import asyncio
import structlog

from ..channels.discord import send_discord
from ..channels.email import send_email
from ..channels.slack import send_slack
from ..channels.telegram import send_telegram
from ..config import settings

logger = structlog.get_logger()

_MAX_RETRIES = 3
_RETRY_DELAY = 5  # seconds between retries


async def _retry(coro_fn, *args, retries: int = _MAX_RETRIES) -> bool:
    for attempt in range(1, retries + 1):
        try:
            ok = await coro_fn(*args)
            if ok:
                return True
        except Exception as exc:
            logger.warning("dispatch_attempt_failed", attempt=attempt, error=str(exc))
        if attempt < retries:
            await asyncio.sleep(_RETRY_DELAY)
    return False


async def dispatch(title: str, body: str, channels: list[str] | None = None) -> dict[str, bool]:
    results: dict[str, bool] = {}
    wanted = set(channels) if channels else None

    if (wanted is None or "discord" in wanted) and settings.DISCORD_WEBHOOK:
        results["discord"] = await _retry(send_discord, settings.DISCORD_WEBHOOK, title, body)

    if (wanted is None or "telegram" in wanted) and settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
        results["telegram"] = await _retry(
            send_telegram, settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID, title, body
        )

    if (wanted is None or "slack" in wanted) and settings.SLACK_WEBHOOK:
        results["slack"] = await _retry(send_slack, settings.SLACK_WEBHOOK, title, body)

    if (wanted is None or "email" in wanted) and settings.SMTP_HOST and settings.SMTP_USER:
        results["email"] = await _retry(
            send_email,
            title,
            body,
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            settings.SMTP_USER,
            settings.SMTP_PASS,
            settings.SMTP_USER,
            settings.SMTP_USER,
        )

    if not results:
        logger.warning("dispatch_no_channels_configured")

    return results

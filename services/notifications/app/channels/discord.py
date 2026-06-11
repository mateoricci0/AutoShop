"""Discord webhook channel."""
from __future__ import annotations

import httpx
import structlog

logger = structlog.get_logger()


async def send_discord(webhook_url: str, title: str, body: str) -> bool:
    payload = {"embeds": [{"title": title, "description": body, "color": 5793266}]}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(webhook_url, json=payload)
            resp.raise_for_status()
        logger.info("discord_sent")
        return True
    except Exception as exc:
        logger.error("discord_send_failed", error=str(exc))
        return False

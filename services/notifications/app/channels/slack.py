"""Slack incoming webhook channel."""
from __future__ import annotations

import httpx
import structlog

logger = structlog.get_logger()


async def send_slack(webhook_url: str, title: str, body: str) -> bool:
    payload = {
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": title}},
            {"type": "section", "text": {"type": "mrkdwn", "text": body}},
        ]
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(webhook_url, json=payload)
            resp.raise_for_status()
        logger.info("slack_sent")
        return True
    except Exception as exc:
        logger.error("slack_send_failed", error=str(exc))
        return False

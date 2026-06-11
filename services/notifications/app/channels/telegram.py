"""Telegram bot channel."""
from __future__ import annotations

import httpx
import structlog

logger = structlog.get_logger()

_TG_API = "https://api.telegram.org/bot{token}/sendMessage"


async def send_telegram(bot_token: str, chat_id: str, title: str, body: str) -> bool:
    text = f"*{title}*\n{body}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                _TG_API.format(token=bot_token),
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            )
            resp.raise_for_status()
        logger.info("telegram_sent", chat_id=chat_id)
        return True
    except Exception as exc:
        logger.error("telegram_send_failed", error=str(exc))
        return False

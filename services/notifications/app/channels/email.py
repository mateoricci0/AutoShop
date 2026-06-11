"""Email channel via SMTP."""
from __future__ import annotations

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import structlog

logger = structlog.get_logger()


async def send_email(
    title: str,
    body: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    from_addr: str,
    to_addr: str,
) -> bool:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = title
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg.attach(MIMEText(body, "plain"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(from_addr, to_addr, msg.as_string())

        logger.info("email_sent", to=to_addr)
        return True
    except Exception as exc:
        logger.error("email_send_failed", error=str(exc))
        return False

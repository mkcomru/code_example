from __future__ import annotations

import httpx
import structlog
from pydantic import SecretStr

from src.backend.modules.notifications.formatting.telegram import format_telegram_message
from src.backend.modules.notifications.schemas import OutboundNotification

log = structlog.get_logger(__name__)


class TelegramHttpAlertChannel:
    """Telegram Bot API sendMessage via HTTPS (no transport module dependency)."""

    def __init__(
        self,
        *,
        bot_token: SecretStr,
        chat_id: str,
        message_thread_id: int | None,
        client: httpx.AsyncClient,
    ) -> None:
        self._token = bot_token
        self._chat_id = chat_id
        self._message_thread_id = message_thread_id
        self._client = client

    async def deliver(self, notification: OutboundNotification) -> None:
        try:
            text = format_telegram_message(notification)
            token = self._token.get_secret_value()
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            body: dict[str, str | int] = {"chat_id": self._chat_id, "text": text}
            if self._message_thread_id is not None:
                body["message_thread_id"] = self._message_thread_id
            response = await self._client.post(url, json=body, timeout=20.0)
            response.raise_for_status()
            payload = response.json()
            if not payload.get("ok"):
                log.error(
                    "alerting.telegram.send_failed",
                    alert_event=notification.event.value,
                    description=payload.get("description"),
                    error_code=payload.get("error_code"),
                )
        except Exception:
            log.exception("alerting.telegram.deliver_failed", alert_event=notification.event.value)

    async def aclose(self) -> None:
        await self._client.aclose()

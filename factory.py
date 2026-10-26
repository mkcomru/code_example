from __future__ import annotations

import httpx

from common import BackendModuleSettings

from src.backend.modules.notifications.channel import AlertChannel
from src.backend.modules.notifications.dispatcher import AlertDispatcher
from src.backend.modules.notifications.telegram_http import TelegramHttpAlertChannel


def build_alert_dispatcher(settings: BackendModuleSettings) -> AlertDispatcher | None:
    channels: list[AlertChannel] = []
    tg = settings.alert.telegram
    token = tg.bot_token
    chat_id = (tg.chat_id or "").strip()
    if tg.enabled and token and chat_id:
        client = httpx.AsyncClient()
        channels.append(
            TelegramHttpAlertChannel(
                bot_token=token,
                chat_id=chat_id,
                message_thread_id=tg.message_thread_id,
                client=client,
            )
        )
    if not channels:
        return None
    return AlertDispatcher(tuple(channels))

from __future__ import annotations

import asyncio

import structlog

from src.backend.modules.notifications.channel import AlertChannel
from src.backend.modules.notifications.schemas import OutboundNotification

log = structlog.get_logger(__name__)


class AlertDispatcher:
    def __init__(self, channels: tuple[AlertChannel, ...]) -> None:
        self._channels = channels
        self._tasks: set[asyncio.Task[None]] = set()

    def schedule_emit(self, notification: OutboundNotification) -> None:
        task = asyncio.create_task(self._emit_all(notification))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _emit_all(self, notification: OutboundNotification) -> None:
        if not self._channels:
            return
        await asyncio.gather(
            *[self._safe_deliver(channel, notification) for channel in self._channels],
            return_exceptions=True,
        )

    async def _safe_deliver(self, channel: AlertChannel, notification: OutboundNotification) -> None:
        try:
            await channel.deliver(notification)
        except Exception:
            log.exception(
                "alerting.channel.deliver_failed",
                channel_type=type(channel).__name__,
                alert_event=notification.event.value,
                **notification.labels,
            )

    async def aclose(self) -> None:
        pending = list(self._tasks)
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        self._tasks.clear()
        for channel in self._channels:
            aclose = getattr(channel, "aclose", None)
            if aclose is not None:
                await aclose()

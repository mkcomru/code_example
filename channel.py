from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.backend.modules.notifications.schemas import OutboundNotification


@runtime_checkable
class AlertChannel(Protocol):
    async def deliver(self, notification: OutboundNotification) -> None:
        """Send one notification; implementations should treat errors as loggable, not reraise."""

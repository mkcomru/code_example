from __future__ import annotations

from src.backend.modules.notifications.channel import AlertChannel
from src.backend.modules.notifications.dependencies import AlertingServiceDep, get_alerting_service
from src.backend.modules.notifications.dispatcher import AlertDispatcher
from src.backend.modules.notifications.events import AlertEvent
from src.backend.modules.notifications.factory import build_alert_dispatcher
from src.backend.modules.notifications.schemas import OutboundNotification, Severity
from src.backend.modules.notifications.service import AlertingService

__all__ = [
    "AlertChannel",
    "AlertDispatcher",
    "AlertEvent",
    "AlertingService",
    "AlertingServiceDep",
    "OutboundNotification",
    "Severity",
    "build_alert_dispatcher",
    "get_alerting_service",
]

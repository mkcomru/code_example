from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from src.backend.modules.core.settings import get_settings
from src.backend.modules.notifications.factory import build_alert_dispatcher
from src.backend.modules.notifications.notification_channels import NotificationInAppChannel
from src.backend.modules.notifications.notification_repository import NotificationRepository
from src.backend.modules.notifications.notification_service import NotificationService
from src.backend.modules.notifications.service import AlertingService
from src.backend.modules.realtime.websocket import get_websocket_manager


@lru_cache(maxsize=1)
def get_alerting_service() -> AlertingService:
    settings = get_settings()
    return AlertingService(build_alert_dispatcher(settings))


@lru_cache(maxsize=1)
def get_notification_service() -> NotificationService:
    ws_manager = get_websocket_manager()
    repo = NotificationRepository()
    channels = (NotificationInAppChannel(ws_manager),)
    return NotificationService(repo, channels, ws_manager)


AlertingServiceDep = Annotated[AlertingService, Depends(get_alerting_service)]
NotificationServiceDep = Annotated[NotificationService, Depends(get_notification_service)]

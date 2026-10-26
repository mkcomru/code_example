from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pydantic import BaseModel

from src.backend.modules.notifications.models import (
    Notification,
    NotificationRecipient,
    RecipientTargetType,
)
from src.backend.modules.users.models import CompanyUser, UserRole

if TYPE_CHECKING:
    from src.backend.modules.realtime.websocket import WebSocketManager


class RecipientTarget(BaseModel):
    type: RecipientTargetType
    user_id: int | None = None
    role: UserRole | None = None
    entity_type: str | None = None
    entity_id: str | None = None


class NotificationChannel(Protocol):
    async def deliver(
        self,
        notification: Notification,
        user: CompanyUser,
        recipient: NotificationRecipient,
    ) -> None: ...


class NotificationInAppChannel:
    def __init__(self, ws_manager: WebSocketManager) -> None:
        self._ws_manager = ws_manager

    async def deliver(
        self,
        notification: Notification,
        user: CompanyUser,
        recipient: NotificationRecipient,
    ) -> None:
        # Realtime user topics are keyed by global User.id, while notification
        # storage and auth remain scoped to CompanyUser.id.
        await self._ws_manager.notify_user_notification(user.user_id, notification, recipient)

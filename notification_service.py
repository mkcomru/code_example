from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from src.backend.modules.notifications.models import Notification, NotificationType, RecipientTargetType
from src.backend.modules.notifications.notification_channels import NotificationChannel, RecipientTarget
from src.backend.modules.notifications.notification_repository import NotificationRepository
from src.backend.modules.orders.models import Order
from src.backend.modules.threads.models import Thread
from src.backend.modules.users.models import CompanyUser, UserRole

if TYPE_CHECKING:
    from src.backend.modules.realtime.websocket import WebSocketManager

log = structlog.get_logger(__name__)


class NotificationService:
    def __init__(
        self,
        repo: NotificationRepository,
        channels: tuple[NotificationChannel, ...],
        ws_manager: WebSocketManager,
    ) -> None:
        self._repo = repo
        self._channels = channels
        self._ws_manager = ws_manager

    @property
    def repo(self) -> NotificationRepository:
        return self._repo

    async def _resolve_targets(self, company_id: int, targets: list[RecipientTarget]) -> list[CompanyUser]:
        users: list[CompanyUser] = []
        seen: set[int] = set()

        for target in targets:
            if target.type == RecipientTargetType.USER:
                if target.user_id is None:
                    raise ValueError("user_id is required for USER target")
                user = await CompanyUser.get_or_none(id=target.user_id, company_id=company_id)
                if user is not None and user.id not in seen:
                    users.append(user)
                    seen.add(user.id)
            elif target.type == RecipientTargetType.ROLE:
                if target.role is None:
                    raise ValueError("role is required for ROLE target")
                role_users = await CompanyUser.filter(company_id=company_id, role=target.role)
                for u in role_users:
                    if u.id not in seen:
                        users.append(u)
                        seen.add(u.id)

        return users

    async def send(
        self,
        company_id: int,
        type: NotificationType,
        title: str,
        body: str,
        payload: dict,
        targets: list[RecipientTarget],
    ) -> Notification:
        notification = await self._repo.create(
            company_id=company_id,
            type=type,
            title=title,
            body=body,
            payload=payload,
        )
        users = await self._resolve_targets(company_id, targets)

        for user in users:
            recipient = await self._repo.add_recipient(notification, user)
            for channel in self._channels:
                try:
                    await channel.deliver(notification, user, recipient)
                except Exception:
                    log.exception(
                        "notification.channel_deliver_failed",
                        channel=channel.__class__.__name__,
                        user_id=user.id,
                        notification_id=notification.id,
                    )

        return notification

    async def notify_handoff_assigned(
        self, order: Order, manager: CompanyUser, thread: Thread | None = None
    ) -> Notification:
        payload: dict = {"order_id": order.id, "order_number": order.order_number}
        if thread is not None:
            payload["thread_id"] = thread.thread_id

        return await self.send(
            company_id=order.company_id,
            type=NotificationType.HANDOFF_ASSIGNED,
            title="Новый чат",
            body=f"Вам передан чат #{order.order_number}",
            payload=payload,
            targets=[RecipientTarget(type=RecipientTargetType.USER, user_id=manager.id)],
        )

    async def notify_balance_empty(self, company_id: int) -> Notification | None:
        existing = await self._repo.get_unresolved_by_type(company_id, NotificationType.BALANCE_EMPTY)
        if existing:
            return None

        return await self.send(
            company_id=company_id,
            type=NotificationType.BALANCE_EMPTY,
            title="Баланс исчерпан",
            body="Баланс компании равен 0. Пополните баланс для продолжения работы.",
            payload={},
            targets=[RecipientTarget(type=RecipientTargetType.ROLE, role=UserRole.OWNER)],
        )

    async def resolve(self, notification_id: int, resolved_by: CompanyUser | None = None) -> None:
        resolved_by_id = resolved_by.id if resolved_by is not None else None
        await self._repo.resolve_notification(notification_id, resolved_by_id)
        recipients = await self._repo.list_recipients(notification_id)
        for recipient in recipients:
            try:
                await self._ws_manager.notify_user_notification_resolved(
                    recipient.company_user.user_id, notification_id
                )
            except Exception:
                log.exception(
                    "notification.resolve_broadcast_failed",
                    notification_id=notification_id,
                    company_user_id=recipient.company_user_id,
                )

    async def resolve_balance_notifications(self, company_id: int) -> None:
        notifications = await self._repo.get_unresolved_by_type(company_id, NotificationType.BALANCE_EMPTY)
        for notification in notifications:
            await self.resolve(notification.id)

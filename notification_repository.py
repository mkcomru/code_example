from __future__ import annotations

from datetime import UTC, datetime

import structlog
from tortoise.functions import Count

from src.backend.modules.notifications.models import (
    Notification,
    NotificationChannelType,
    NotificationRecipient,
    NotificationType,
    UserNotificationPreferences,
)
from src.backend.modules.users.models import CompanyUser

log = structlog.get_logger(__name__)


class NotificationRepository:
    async def create(
        self,
        company_id: int,
        type: NotificationType,
        title: str,
        body: str,
        payload: dict,
    ) -> Notification:
        return await Notification.create(
            company_id=company_id,
            type=type,
            title=title,
            body=body,
            payload=payload,
        )

    async def add_recipient(self, notification: Notification, user: CompanyUser) -> NotificationRecipient:
        return await NotificationRecipient.create(
            notification=notification,
            company_user=user,
        )

    async def list_for_user(
        self,
        company_user_id: int,
        company_id: int,
        limit: int,
        offset: int,
        *,
        unread_only: bool = False,
    ) -> list[NotificationRecipient]:
        qs = NotificationRecipient.filter(
            company_user_id=company_user_id,
            notification__company_id=company_id,
        )
        if unread_only:
            qs = qs.filter(is_read=False)
        return await qs.select_related("notification").order_by("-notification__created_at").limit(limit).offset(offset)

    async def count_for_user(
        self,
        company_user_id: int,
        company_id: int,
        *,
        unread_only: bool = False,
    ) -> int:
        qs = NotificationRecipient.filter(
            company_user_id=company_user_id,
            notification__company_id=company_id,
        )
        if unread_only:
            qs = qs.filter(is_read=False)
        return await qs.count()

    async def mark_read(self, recipient_id: int, company_user_id: int) -> NotificationRecipient:
        recipient = await NotificationRecipient.get(id=recipient_id, company_user_id=company_user_id)
        if not recipient.is_read:
            recipient.is_read = True
            recipient.read_at = datetime.now(UTC)
            await recipient.save(update_fields=["is_read", "read_at"])
        return recipient

    async def mark_all_read(self, company_user_id: int, company_id: int) -> int:
        now = datetime.now(UTC)
        # Fetch IDs first to avoid UPDATE...JOIN which SQLite does not support
        ids = await NotificationRecipient.filter(
            company_user_id=company_user_id,
            notification__company_id=company_id,
            is_read=False,
        ).values_list("id", flat=True)
        if not ids:
            return 0
        return await NotificationRecipient.filter(id__in=ids).update(is_read=True, read_at=now)

    async def unread_count(self, company_user_id: int, company_id: int) -> int:
        return await NotificationRecipient.filter(
            company_user_id=company_user_id,
            notification__company_id=company_id,
            is_read=False,
        ).count()

    async def unread_counts_by_company(self, company_user_ids: list[int]) -> dict[int, int]:
        rows = (
            await NotificationRecipient.filter(
                company_user_id__in=company_user_ids,
                is_read=False,
            )
            .annotate(count=Count("id"))
            .group_by("company_user_id")
            .values("company_user_id", "count")
        )
        return {row["company_user_id"]: row["count"] for row in rows}

    async def get_unresolved_by_type(self, company_id: int, type: NotificationType) -> list[Notification]:
        return await Notification.filter(company_id=company_id, type=type, resolved_at=None).all()

    async def list_recipients(self, notification_id: int) -> list[NotificationRecipient]:
        return await NotificationRecipient.filter(notification_id=notification_id).select_related("company_user").all()

    async def resolve_notification(self, notification_id: int, resolved_by_id: int | None = None) -> Notification:
        notification = await Notification.get(id=notification_id)
        notification.resolved_at = datetime.now(UTC)
        notification.resolved_by_id = resolved_by_id
        await notification.save(update_fields=["resolved_at", "resolved_by_id"])
        return notification

    async def get_user_channels(self, company_user_id: int) -> list[NotificationChannelType]:
        prefs = await UserNotificationPreferences.get_or_none(company_user_id=company_user_id)
        if prefs is None:
            return [NotificationChannelType.INAPP]
        return [NotificationChannelType(c) for c in prefs.channels]

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from src.backend.modules.notifications.models import Notification, NotificationRecipient, NotificationType


class NotificationResponse(BaseModel):
    id: int
    company_id: int
    type: NotificationType
    title: str
    body: str
    payload: dict
    created_at: datetime
    resolved_at: datetime | None

    @classmethod
    def from_model(cls, notification: Notification) -> NotificationResponse:
        return cls(
            id=notification.id,
            company_id=notification.company_id,
            type=notification.type,
            title=notification.title,
            body=notification.body,
            payload=notification.payload,
            created_at=notification.created_at,
            resolved_at=notification.resolved_at,
        )


class NotificationRecipientResponse(BaseModel):
    id: int
    notification: NotificationResponse
    is_read: bool
    read_at: datetime | None

    @classmethod
    def from_model(cls, recipient: NotificationRecipient) -> NotificationRecipientResponse:
        return cls(
            id=recipient.id,
            notification=NotificationResponse.from_model(recipient.notification),
            is_read=recipient.is_read,
            read_at=recipient.read_at,
        )


class NotificationListResponse(BaseModel):
    items: list[NotificationRecipientResponse]
    total: int
    unread_count: int


class MarkAllReadResponse(BaseModel):
    updated: int


class UnreadCountResponse(BaseModel):
    count: int


class CompanyNotificationSummary(BaseModel):
    company_id: int
    unread_count: int

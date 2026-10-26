from __future__ import annotations

from enum import StrEnum

from tortoise import fields

from src.backend.modules.core.base_model import BaseModel


class NotificationType(StrEnum):
    HANDOFF_ASSIGNED = "handoff_assigned"
    BALANCE_EMPTY = "balance_empty"


class NotificationChannelType(StrEnum):
    INAPP = "inapp"
    TELEGRAM = "telegram"
    EMAIL = "email"


class RecipientTargetType(StrEnum):
    USER = "user"
    ROLE = "role"
    ENTITY = "entity"


class Notification(BaseModel):
    id = fields.IntField(primary_key=True)
    company_id = fields.IntField()
    type = fields.CharEnumField(NotificationType, max_length=50)
    title = fields.CharField(max_length=255)
    body = fields.TextField()
    payload = fields.JSONField(default=dict)
    created_at = fields.DatetimeField(auto_now_add=True)
    resolved_at = fields.DatetimeField(null=True)
    resolved_by: fields.ForeignKeyNullableRelation = fields.ForeignKeyField(
        "models.CompanyUser",
        related_name="resolved_notifications",
        on_delete=fields.SET_NULL,
        null=True,
    )

    recipients: fields.ReverseRelation

    class Meta(BaseModel.Meta):
        table = "notifications"


class NotificationRecipient(BaseModel):
    id = fields.IntField(primary_key=True)
    notification: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "models.Notification",
        related_name="recipients",
        on_delete=fields.CASCADE,
    )
    company_user: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "models.CompanyUser",
        related_name="notification_recipients",
        on_delete=fields.CASCADE,
    )
    is_read = fields.BooleanField(default=False)
    read_at = fields.DatetimeField(null=True)

    class Meta(BaseModel.Meta):
        table = "notification_recipients"
        indexes = (("notification_id", "company_user_id"),)


class UserNotificationPreferences(BaseModel):
    id = fields.IntField(primary_key=True)
    company_user: fields.OneToOneRelation = fields.OneToOneField(
        "models.CompanyUser",
        related_name="notification_preferences",
        on_delete=fields.CASCADE,
    )
    channels = fields.JSONField(default=list)

    class Meta(BaseModel.Meta):
        table = "user_notification_preferences"

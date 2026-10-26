from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from src.backend.modules.notifications.events import AlertEvent


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class OutboundNotification(BaseModel):
    """Backend-originated alert or notice for outbound delivery (monitor rules, billing, etc.)."""

    event: AlertEvent
    severity: Severity
    summary: str
    labels: dict[str, str]
    context: dict[str, str | int | float] = Field(default_factory=dict)

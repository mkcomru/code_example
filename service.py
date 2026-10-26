from __future__ import annotations

from typing import Literal

import structlog

from src.backend.modules.notifications.dispatcher import AlertDispatcher
from src.backend.modules.notifications.events import AlertEvent
from src.backend.modules.notifications.schemas import OutboundNotification, Severity
from src.backend.modules.threads.exceptions import AmbiguousThreadConversationError

log = structlog.get_logger(__name__)

BillingBlockReason = Literal["charge_failed", "zero_balance"]


class AlertingService:
    """Application entry for outbound alerts; no-ops when no channels are configured."""

    def __init__(self, dispatcher: AlertDispatcher | None) -> None:
        self._dispatcher = dispatcher

    def schedule_emit(self, notification: OutboundNotification) -> None:
        if self._dispatcher is None:
            return
        log.info(
            "alerting.scheduled",
            alert_event=notification.event.value,
            severity=notification.severity.value,
            **notification.labels,
        )
        self._dispatcher.schedule_emit(notification)

    def notify_billing_blocked_sales_agent(
        self,
        *,
        company_id: int,
        thread_id: str,
        order_id: int,
        connector_id: str,
        block_reason: BillingBlockReason,
        balance: int,
    ) -> None:
        detail = "Sales agent was not run: insufficient balance. MVP — contact the customer for payment manually."
        payload = OutboundNotification(
            event=AlertEvent.BILLING_BLOCKS_SALES_AGENT,
            severity=Severity.WARNING,
            summary=detail,
            labels={
                "company_id": str(company_id),
                "thread_id": thread_id,
                "order_id": str(order_id),
            },
            context={
                "block_reason": block_reason,
                "balance": balance,
                "connector_id": connector_id,
            },
        )
        self.schedule_emit(payload)

    def notify_thread_conversation_ambiguous(
        self,
        exc: AmbiguousThreadConversationError,
        *,
        request_path: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        payload = OutboundNotification(
            event=AlertEvent.THREAD_CONVERSATION_AMBIGUOUS,
            severity=Severity.CRITICAL,
            summary="Multiple threads match the same conversation; inbound rejected (manual resolution required).",
            labels={
                "company_id": str(exc.company_id),
                "customer_id": str(exc.customer_id),
                "channel_type": exc.channel_type,
                "conversation_id": exc.conversation_id,
            },
            context={
                "user_id": exc.user_id,
                "ingress_connector_id": exc.ingress_connector_id or "",
                "conflicting_thread_ids": ",".join(exc.conflicting_thread_ids),
                "request_path": request_path or "",
                "correlation_id": correlation_id or "",
            },
        )
        self.schedule_emit(payload)

    async def aclose(self) -> None:
        if self._dispatcher is None:
            return
        await self._dispatcher.aclose()

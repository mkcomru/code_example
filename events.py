from __future__ import annotations

from enum import StrEnum


class AlertEvent(StrEnum):
    """Stable ids for outbound alerts; values MUST stay aligned with monitor rule names and ops tooling."""

    ACTIVE_ASSISTANT_REPLY_STALL = "active_assistant_reply_stall"
    HEAVY_ASSISTANT_TRAFFIC = "heavy_assistant_traffic"
    BILLING_BLOCKS_SALES_AGENT = "billing_blocks_sales_agent"
    COMPANY_METRICS_MISSING_TARGET = "company_metrics_missing_target"
    THREAD_CONVERSATION_AMBIGUOUS = "thread_conversation_ambiguous"

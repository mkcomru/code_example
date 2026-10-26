from __future__ import annotations

from src.backend.modules.notifications.events import AlertEvent
from src.backend.modules.notifications.formatting import text as fmt
from src.backend.modules.notifications.formatting.shortcuts import AlertShortcutContext, default_shortcut_context
from src.backend.modules.notifications.schemas import OutboundNotification


def format_telegram_message(
    notification: OutboundNotification,
    *,
    shortcuts: AlertShortcutContext | None = None,
) -> str:
    sc = shortcuts if shortcuts is not None else default_shortcut_context()
    match notification.event:
        case AlertEvent.ACTIVE_ASSISTANT_REPLY_STALL:
            return _format_assistant_reply_stall(notification, sc)
        case AlertEvent.HEAVY_ASSISTANT_TRAFFIC:
            return _format_heavy_assistant_traffic(notification, sc)
        case AlertEvent.BILLING_BLOCKS_SALES_AGENT:
            return _format_billing_blocks_sales_agent(notification, sc)
        case AlertEvent.THREAD_CONVERSATION_AMBIGUOUS:
            return _format_thread_conversation_ambiguous(notification, sc)
        case _:
            return _format_generic(notification)


def _format_assistant_reply_stall(n: OutboundNotification, sc: AlertShortcutContext) -> str:
    lines = [
        f"[{n.severity.value.upper()}] Assistant reply stall",
        n.summary,
        "",
        "Thread:",
        *fmt.indented_kv_lines(
            {
                "company_id": n.labels["company_id"],
                "thread_id": n.labels["thread_id"],
                "user_message_id": n.labels["user_message_id"],
            }
        ),
        *sc.inbox_thread_link_lines(n.labels["company_id"], n.labels["thread_id"]),
    ]
    if n.context:
        lines.extend(["", "Timing / connector:", *fmt.indented_context_lines(n.context)])
    return fmt.truncate_plain_text("\n".join(lines))


def _format_heavy_assistant_traffic(n: OutboundNotification, sc: AlertShortcutContext) -> str:
    params_lines = fmt.indented_context_lines(n.context) if n.context else []
    lines = [
        f"[{n.severity.value.upper()}] Heavy assistant traffic",
        n.summary,
        "",
        "Thread:",
        *fmt.indented_kv_lines(
            {
                "company_id": n.labels["company_id"],
                "thread_id": n.labels["thread_id"],
                "last_assistant_message_id": n.labels["last_assistant_message_id"],
            }
        ),
        *sc.inbox_thread_link_lines(n.labels["company_id"], n.labels["thread_id"]),
    ]
    if params_lines:
        lines.extend(["", "Threshold:", *params_lines])
    return fmt.truncate_plain_text("\n".join(lines))


def _format_thread_conversation_ambiguous(n: OutboundNotification, sc: AlertShortcutContext) -> str:
    lines = [
        f"[{n.severity.value.upper()}] Ambiguous thread / conversation match",
        n.summary,
        "",
        "Conversation:",
        *fmt.indented_kv_lines(
            {
                "company_id": n.labels["company_id"],
                "customer_id": n.labels["customer_id"],
                "channel_type": n.labels["channel_type"],
                "conversation_id": n.labels["conversation_id"],
            }
        ),
    ]
    if n.context:
        lines.extend(["", "Diagnostics:", *fmt.indented_context_lines(n.context)])
    first_thread = str(n.context.get("conflicting_thread_ids", "")).split(",")[0]
    if first_thread:
        lines.extend(sc.inbox_thread_link_lines(n.labels["company_id"], first_thread))
    return fmt.truncate_plain_text("\n".join(lines))


def _format_billing_blocks_sales_agent(n: OutboundNotification, sc: AlertShortcutContext) -> str:
    block = str(n.context.get("block_reason", ""))
    bal = n.context.get("balance", "")
    lines = [
        f"[{n.severity.value.upper()}] Billing: sales agent blocked",
        n.summary,
        "",
        "Where:",
        *fmt.indented_kv_lines(
            {
                "company_id": n.labels["company_id"],
                "thread_id": n.labels["thread_id"],
                "order_id": n.labels["order_id"],
                "connector_id": str(n.context.get("connector_id", "")),
            }
        ),
        "",
        "Details:",
        f"  block_reason: {block}",
        f"  balance: {bal}",
        *sc.inbox_thread_link_lines(n.labels["company_id"], n.labels["thread_id"]),
    ]
    return fmt.truncate_plain_text("\n".join(lines))


def _format_generic(n: OutboundNotification) -> str:
    lines = [
        f"[{n.severity.value.upper()}] {n.event.value}",
        n.summary,
        "",
        "Labels:",
        *fmt.indented_kv_lines(n.labels),
    ]
    if n.context:
        lines.extend(["", "Context:", *fmt.indented_context_lines(n.context)])
    return fmt.truncate_plain_text("\n".join(lines))

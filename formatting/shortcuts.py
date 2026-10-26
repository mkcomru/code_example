"""Deep-link helpers for operator-facing alert channels (Telegram, etc.).

Add URL builders here as new alert types need jump targets. Formatters take
``AlertShortcutContext`` so tests stay pure without loading settings.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

from src.backend.modules.core.settings import get_settings


def normalize_frontend_host(raw: str | None) -> str | None:
    """Return host only, no scheme or path. None when unset."""
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    for prefix in ("https://", "http://"):
        if text.startswith(prefix):
            text = text[len(prefix) :]
            break
    text = text.split("/")[0]
    return text.rstrip("/") or None


@dataclass(frozen=True)
class AlertShortcutContext:
    """Resolved frontend origin for building operator URLs."""

    frontend_host: str | None

    def inbox_thread_url(self, company_id: str | int, thread_id: str) -> str | None:
        """Inbox focused on a thread: ``/{company_id}/inbox?thread=...``."""
        if not self.frontend_host:
            return None
        cid = str(company_id).strip()
        tid = str(thread_id).strip()
        if not cid or not tid:
            return None
        return f"https://{self.frontend_host}/{cid}/inbox?{urlencode({'thread': tid})}"

    def inbox_thread_link_lines(self, company_id: str | int, thread_id: str) -> list[str]:
        url = self.inbox_thread_url(company_id, thread_id)
        if url is None:
            return []
        return ["", "Open in app:", f"  {url}"]


def default_shortcut_context() -> AlertShortcutContext:
    return AlertShortcutContext(frontend_host=normalize_frontend_host(get_settings().domain_frontend))

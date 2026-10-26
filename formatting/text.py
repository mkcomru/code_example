from __future__ import annotations

_TELEGRAM_MESSAGE_MAX_CHARS = 4096


def truncate_plain_text(
    text: str, max_chars: int = _TELEGRAM_MESSAGE_MAX_CHARS, *, suffix: str = "\n…(truncated)"
) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - len(suffix)] + suffix


def indented_kv_lines(data: dict[str, str], *, indent: str = "  ") -> list[str]:
    return [f"{indent}{k}: {v}" for k, v in sorted(data.items())]


def indented_context_lines(context: dict[str, str | int | float], *, indent: str = "  ") -> list[str]:
    return [f"{indent}{k}: {v}" for k, v in sorted(context.items(), key=lambda x: x[0])]

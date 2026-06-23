from __future__ import annotations

from platform_core.state_store import platform_history
from execution.thinking import thinking_timeline


def action_trace(limit: int = 80) -> list[dict]:
    events = platform_history(limit=limit)
    thinking = thinking_timeline()

    for event in events:
        event.setdefault("source", "platform")
    for item in thinking:
        item.setdefault("source", "thinking")

    merged = events + thinking
    merged.sort(key=lambda item: item.get("createdAt") or item.get("timestamp") or "", reverse=True)

    seen: set[str] = set()
    result: list[dict] = []
    for item in merged:
        key = str(item.get("message") or item.get("event") or item.get("kind") or "")
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        result.append(item)

    return result[:limit]

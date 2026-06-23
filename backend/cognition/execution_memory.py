from __future__ import annotations

from api.memory_storage import recent_memories
from platform_core.state_store import platform_history


def execution_memory(limit: int = 80) -> list[dict]:
    events = platform_history(limit=limit // 2)
    memories = recent_memories(limit=limit // 2)

    for event in events:
        event.setdefault("layer", "short_term")
    for memory in memories:
        memory.setdefault("layer", "long_term")

    merged = events + memories
    merged.sort(key=lambda item: item.get("createdAt") or item.get("timestamp") or item.get("created_at") or "", reverse=True)
    return merged[:limit]

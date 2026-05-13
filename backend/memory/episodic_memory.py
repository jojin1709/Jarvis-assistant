from __future__ import annotations

from api.memory_storage import recent_memories, remember_event


def remember_episode(title: str, content: str, metadata: dict | None = None) -> None:
    remember_event("workflows", title, content, metadata or {})


def recent_episodes(limit: int = 12) -> list[dict]:
    return recent_memories(limit=limit, kind="workflows")

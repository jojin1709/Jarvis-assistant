from __future__ import annotations

from events.event_bus import emit_event, recent_events


def record_reasoning(phase: str, summary: str, metadata: dict | None = None) -> dict:
    return emit_event("reasoning_trace", {"phase": phase, "summary": summary, "metadata": metadata or {}})


def reasoning_timeline(limit: int = 80) -> list[dict]:
    return [event for event in recent_events(limit=limit) if event.get("kind") == "reasoning_trace"]

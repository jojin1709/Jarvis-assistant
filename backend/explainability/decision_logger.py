from __future__ import annotations

from events.event_bus import emit_event


def log_decision(kind: str, reason: str, metadata: dict | None = None) -> dict:
    return emit_event("decision_logged", {"kind": kind, "reason": reason, "metadata": metadata or {}})

from __future__ import annotations

from platform_core.state_store import platform_history


def action_trace(limit: int = 80) -> list[dict]:
    return platform_history(limit=limit)

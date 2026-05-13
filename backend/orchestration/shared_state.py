from __future__ import annotations

from platform_core.state_store import platform_history, platform_state, update_platform_state


def get_shared_state() -> dict:
    return {"state": platform_state(), "history": platform_history(limit=60)}


def update_shared_state(patch: dict) -> dict:
    return update_platform_state(patch)

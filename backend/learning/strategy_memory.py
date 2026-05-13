from __future__ import annotations

from learning.behavior import learning_state, record_behavior


def remember_strategy(strategy_id: str, ok: bool, metadata: dict | None = None) -> dict:
    return record_behavior("strategy", strategy_id, "success" if ok else "failure", metadata or {})


def strategy_preferences() -> list[dict]:
    return learning_state().get("preferences", {}).get("strategy", [])

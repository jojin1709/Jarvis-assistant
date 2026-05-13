from __future__ import annotations

from learning.behavior import learning_state


def strategy_history() -> dict:
    prefs = learning_state().get("preferences", {})
    return {"strategies": prefs.get("strategy", []), "taskTypes": prefs.get("task_type", [])}

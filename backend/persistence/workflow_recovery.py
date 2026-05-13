from __future__ import annotations

from platform_core.state_store import platform_state
from persistence.task_checkpoint import latest_checkpoints


def recovery_candidates() -> dict:
    state = platform_state()
    active = state.get("activeTask")
    interrupted = [task for task in state.get("recentTasks", []) if task.get("status") not in {"completed", "failed"}]
    return {"activeTask": active, "interruptedTasks": interrupted, "checkpoints": latest_checkpoints()}

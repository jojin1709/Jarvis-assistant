from __future__ import annotations

from platform_core.state_store import update_platform_state
from persistence.task_checkpoint import load_checkpoint


def restore_platform_state(task_id: str) -> dict:
    checkpoint = load_checkpoint(task_id)
    if not checkpoint:
        return {"ok": False, "error": "Checkpoint not found."}
    state = checkpoint.get("state") or {}
    update_platform_state({"activeTask": state.get("activeTask"), "restoredFrom": task_id})
    return {"ok": True, "restoredFrom": task_id}

from __future__ import annotations

from persistence.task_checkpoint import load_checkpoint


def resume_from_checkpoint(task_id: str) -> dict:
    checkpoint = load_checkpoint(task_id)
    if not checkpoint:
        return {"ok": False, "error": "Checkpoint not found."}
    return {"ok": True, "checkpoint": checkpoint, "message": "Checkpoint loaded; execution can be replanned from saved state."}

from __future__ import annotations

from learning.behavior import record_behavior


def record_workflow_result(workflow_id: str, ok: bool, metadata: dict | None = None) -> dict:
    return record_behavior("workflow", workflow_id, "success" if ok else "failure", metadata or {})

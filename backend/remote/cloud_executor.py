from __future__ import annotations

from remote.task_distribution import distribution_plan


def cloud_execution_preview(task: dict) -> dict:
    plan = distribution_plan(task)
    return {"ok": True, "willExecute": False, "plan": plan, "message": "Remote execution is optional and disabled until a trusted worker is enabled."}

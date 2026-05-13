from __future__ import annotations

from optimization.resource_optimizer import resource_plan


def performance_status() -> dict:
    plan = resource_plan()
    return {"ok": True, "plan": plan, "mode": "conservative" if plan["maxParallelTasks"] == 1 else "balanced"}

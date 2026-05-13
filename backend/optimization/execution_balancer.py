from __future__ import annotations

from optimization.resource_optimizer import resource_plan


def balance_execution(tasks: list[dict]) -> dict:
    plan = resource_plan()
    max_parallel = plan["maxParallelTasks"]
    return {"parallel": tasks[:max_parallel], "queued": tasks[max_parallel:], "resourcePlan": plan}

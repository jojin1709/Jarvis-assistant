from __future__ import annotations

from optimization.resource_optimizer import resource_plan


def async_runtime_plan(pending_tasks: int = 0) -> dict:
    resources = resource_plan()
    max_parallel = int(resources.get("maxParallelTasks", 1))
    throttle = pending_tasks > max_parallel * 2
    return {
        "maxParallelTasks": max_parallel,
        "pendingTasks": pending_tasks,
        "throttleHeavyWorkflows": throttle,
        "recommendedBatchSize": max(1, min(max_parallel, pending_tasks or max_parallel)),
    }

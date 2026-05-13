from __future__ import annotations

from optimization.resource_optimizer import resource_plan


PRIORITY = {"SafetyAgent": 100, "ExecutiveAgent": 95, "PlannerAgent": 80, "CodingAgent": 70, "BrowserAgent": 65, "ResearchAgent": 55}


def schedule_agents(tasks: list[dict]) -> dict:
    plan = resource_plan()
    ordered = sorted(tasks, key=lambda task: (-PRIORITY.get(str(task.get("agent") or ""), 40), str(task.get("createdAt") or "")))
    parallel = max(1, int(plan.get("maxParallelTasks", 1)))
    return {"maxParallel": parallel, "ready": ordered[:parallel], "queued": ordered[parallel:], "resourcePlan": plan}

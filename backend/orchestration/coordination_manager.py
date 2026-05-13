from __future__ import annotations

from orchestration.agent_bus import publish_agent_event
from orchestration.execution_graph import build_execution_graph
from orchestration.task_router import route_tasks


def coordinate_goal(goal: str, cognitive_plan: dict | None = None) -> dict:
    graph = build_execution_graph(goal)
    routed = route_tasks(graph["nodes"])
    publish_agent_event("coordination_manager", "orchestrator", "goal.coordinated", {"goal": goal, "routes": routed})
    return {"graph": graph, "routedSteps": routed, "plan": cognitive_plan or {}}

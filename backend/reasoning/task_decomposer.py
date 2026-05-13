from __future__ import annotations

from planner.engine import build_task_graph


def decompose_goal(goal: str) -> dict:
    graph = build_task_graph(goal)
    return {
        "goal": graph.goal,
        "createdAt": graph.created_at,
        "steps": [step.__dict__ for step in graph.steps],
        "stepCount": len(graph.steps),
        "agents": list(dict.fromkeys(step.agent for step in graph.steps)),
    }

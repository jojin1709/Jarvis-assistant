from __future__ import annotations

from planner.engine import build_task_graph


def build_execution_graph(goal: str) -> dict:
    graph = build_task_graph(goal)
    nodes = [step.__dict__ for step in graph.steps]
    edges = [{"from": dep, "to": step.id} for step in graph.steps for dep in step.depends_on]
    return {"goal": graph.goal, "createdAt": graph.created_at, "nodes": nodes, "edges": edges}

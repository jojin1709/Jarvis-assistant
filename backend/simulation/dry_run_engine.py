from __future__ import annotations

from reasoning.planning_engine import build_cognitive_plan
from simulation.impact_analyzer import estimate_impact


def dry_run_goal(goal: str, intelligence: dict | None = None) -> dict:
    plan = build_cognitive_plan(goal, intelligence or {"context": {"world": {}}})
    return {"ok": True, "goal": goal, "plan": plan, "impact": estimate_impact(plan), "willExecute": False}

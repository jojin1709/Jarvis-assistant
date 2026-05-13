from __future__ import annotations

from reasoning.planning_engine import build_cognitive_plan
from simulation.dry_run_engine import dry_run_goal


def reason_about_goal(goal: str, brain: dict, dry_run: bool = False) -> dict:
    if dry_run:
        return dry_run_goal(goal, brain.get("intelligence") or {})
    return {"ok": True, "plan": build_cognitive_plan(goal, brain.get("intelligence") or {})}

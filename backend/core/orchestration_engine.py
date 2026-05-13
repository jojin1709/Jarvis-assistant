from __future__ import annotations

from orchestration.coordination_manager import coordinate_goal
from skills.registry import select_skills


def orchestrate(goal: str, cognitive_plan: dict) -> dict:
    return {"coordination": coordinate_goal(goal, cognitive_plan), "skills": select_skills(goal)}

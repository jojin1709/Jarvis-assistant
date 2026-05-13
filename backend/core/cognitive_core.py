from __future__ import annotations

from core.contextual_brain import build_contextual_brain
from core.orchestration_engine import orchestrate
from core.reasoning_controller import reason_about_goal
from optimization.performance_manager import performance_status
from recovery.environment_restore import restore_readiness


def cognitive_core_status() -> dict:
    return {"ok": True, "performance": performance_status(), "recovery": restore_readiness()}


def prepare_goal(goal: str, include_vision: bool = False, dry_run: bool = False) -> dict:
    brain = build_contextual_brain(goal, include_vision=include_vision)
    reasoning = reason_about_goal(goal, brain, dry_run=dry_run)
    plan = reasoning.get("plan") or reasoning.get("plan", {})
    orchestration = orchestrate(goal, plan) if plan else {}
    return {"brain": brain, "reasoning": reasoning, "orchestration": orchestration}

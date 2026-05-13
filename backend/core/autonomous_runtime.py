from __future__ import annotations

from core.cognitive_core import prepare_goal
from core.execution_manager import execute_with_controls
from events.event_dispatcher import dispatch
from explainability.reasoning_explainer import explain_reasoning
from recovery.snapshot_engine import create_snapshot


def run_autonomous_runtime(goal: str, include_vision: bool = False, dry_run: bool = False) -> dict:
    dispatch("task_received", {"goal": goal})
    prepared = prepare_goal(goal, include_vision=include_vision, dry_run=dry_run)
    plan = prepared.get("reasoning", {}).get("plan") or prepared.get("reasoning", {}).get("plan", {})
    if dry_run:
        return {"ok": True, "goal": goal, "dryRun": True, **prepared}
    snapshot = create_snapshot(f"before-{goal[:40]}", paths=[])
    result = execute_with_controls(goal, prepared.get("brain", {}), plan)
    explanation = explain_reasoning(result.get("cognitivePlan", plan if isinstance(plan, dict) else {}))
    return {"ok": result.get("ok"), "goal": goal, "response": result.get("response"), "result": result, "prepared": prepared, "snapshot": snapshot, "explanation": explanation}

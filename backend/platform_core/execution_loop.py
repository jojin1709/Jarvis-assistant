from __future__ import annotations

from core.autonomous_runtime import run_autonomous_runtime


def execute_platform_goal(goal: str, include_vision: bool = False) -> dict:
    result = run_autonomous_runtime(goal, include_vision=include_vision)
    return {"ok": result.get("ok"), "result": result, "intelligence": result.get("prepared", {}).get("brain", {}).get("intelligence", {})}

from __future__ import annotations

from decision_engine.retry_planner import plan_retry
from reflection.failure_analyzer import analyze_failure


def reflective_retry_plan(message: str, attempt: int, context: dict | None = None) -> dict:
    failure = analyze_failure(message, context)
    retry = plan_retry(message, attempt)
    if failure["category"] == "safety_gate":
        retry["retry"] = False
    if failure["category"] == "code_or_build":
        retry["strategy"] = "self_heal"
    return {"failure": failure, "retry": retry}

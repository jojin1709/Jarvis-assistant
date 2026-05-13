from __future__ import annotations

from learning.behavior import record_behavior


def learn_from_execution(goal: str, review: dict, strategy: dict | None = None) -> dict:
    outcome = "success" if review.get("score", 0) >= 70 and not review.get("failedSteps") else "failure"
    strategy_id = (strategy or {}).get("id") or "unknown"
    event = record_behavior("strategy", strategy_id, outcome, {"goal": goal, "review": review})
    return {"learned": True, "outcome": outcome, "event": event}

from __future__ import annotations

from decision_engine.retry_planner import plan_retry
from execution.thinking import thinking_timeline
from learning.behavior import record_behavior


def analyze_execution_quality(logs: list[dict] | None = None, record: bool = False) -> dict:
    logs = logs or thinking_timeline()
    failures = [log for log in logs if str(log.get("level") or "").lower() in {"error", "failed"} or "failed" in str(log.get("message", "")).lower()]
    successes = [log for log in logs if str(log.get("level") or "").lower() == "success"]
    recommendations = []
    for failure in failures[-8:]:
        retry = plan_retry(str(failure.get("message") or ""), 1)
        recommendations.append({"failure": failure.get("message"), "retry": retry})
    score = max(0, min(100, 70 + len(successes) * 3 - len(failures) * 8))
    if record:
        record_behavior("execution_score", str(score), "success" if score >= 70 else "failure")
    return {"score": score, "successes": len(successes), "failures": len(failures), "recommendations": recommendations}

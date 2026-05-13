from __future__ import annotations

from reflection.failure_analyzer import analyze_failure


def review_execution(result: dict) -> dict:
    steps = ((result or {}).get("result") or result or {}).get("graph", {}).get("steps", [])
    failures = [step for step in steps if step.get("status") == "failed"]
    completed = [step for step in steps if step.get("status") == "completed"]
    score = max(0, min(100, 50 + len(completed) * 12 - len(failures) * 20))
    return {
        "score": score,
        "completedSteps": len(completed),
        "failedSteps": len(failures),
        "failureAnalysis": [analyze_failure(step.get("result", "")) for step in failures],
        "summary": "Execution completed cleanly." if not failures else "Execution needs adaptation before retry.",
    }

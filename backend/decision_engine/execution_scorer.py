from __future__ import annotations


def score_execution_plan(plan: dict, context_analysis: dict | None = None) -> dict:
    steps = plan.get("taskGraph", {}).get("steps", [])
    constraints = (context_analysis or plan.get("contextAnalysis") or {}).get("constraints", [])
    risk_penalty = sum({"low": 1, "medium": 4, "high": 10}.get(step.get("risk", "low"), 3) for step in steps)
    score = max(0, min(100, 85 - risk_penalty - len(constraints) * 8 + min(len(steps), 6) * 2))
    return {"score": score, "stepCount": len(steps), "constraintCount": len(constraints), "confidence": round(score / 100, 2)}

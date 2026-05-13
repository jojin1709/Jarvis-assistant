from __future__ import annotations


def estimate_impact(plan: dict) -> dict:
    steps = plan.get("taskGraph", {}).get("steps") or plan.get("nodes") or []
    risks = [step.get("risk", "low") for step in steps]
    return {
        "stepCount": len(steps),
        "riskCounts": {risk: risks.count(risk) for risk in sorted(set(risks))},
        "requiresApprovalLikely": "high" in risks,
    }

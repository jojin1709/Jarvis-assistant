from __future__ import annotations


def explain_reasoning(cognitive_plan: dict) -> dict:
    trace = cognitive_plan.get("reasoningTrace") or []
    return {"summary": " -> ".join(item.get("phase", "") for item in trace), "trace": trace}

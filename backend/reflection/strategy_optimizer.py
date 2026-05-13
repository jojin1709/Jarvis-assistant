from __future__ import annotations


def optimize_strategy(plan: dict, review: dict) -> dict:
    selected = dict(plan.get("selectedStrategy") or {})
    adaptations = []
    if review.get("failedSteps"):
        adaptations.append("Prefer lower-risk tool sequence and collect observations before next execution.")
        selected["confidence"] = round(max(0.3, float(selected.get("confidence", 0.5)) - 0.12), 2)
    if any(item.get("category") == "code_or_build" for item in review.get("failureAnalysis", [])):
        adaptations.append("Insert coding self-heal and build verification before browser preview.")
        selected["id"] = "engineer_debug_loop"
    if any(item.get("category") == "safety_gate" for item in review.get("failureAnalysis", [])):
        adaptations.append("Stop autonomous retries until permission is approved.")
        selected["requiresApproval"] = True
    return {"strategy": selected, "adaptations": adaptations}

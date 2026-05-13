from __future__ import annotations


def optimize_workflow(workflow: dict, failures: list[dict] | None = None) -> dict:
    failures = failures or []
    suggestions = []
    if any("timeout" in str(item).lower() for item in failures):
        suggestions.append("Increase timeout on long-running terminal or browser nodes.")
    if any("login" in str(item).lower() for item in failures):
        suggestions.append("Insert a manual-login checkpoint before browser provider nodes.")
    if not workflow.get("edges") and len(workflow.get("nodes", [])) > 1:
        suggestions.append("Connect nodes explicitly so execution order is stable.")
    return {"workflowId": workflow.get("id"), "suggestions": suggestions, "score": max(0, 100 - len(failures) * 15)}

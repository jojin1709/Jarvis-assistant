from __future__ import annotations

from workflows.workflow_parser import execution_order, validate_workflow


def simulate_workflow(workflow: dict) -> dict:
    ok, message, normalized = validate_workflow(workflow)
    if not ok:
        return {"ok": False, "error": message}
    ordered = execution_order(normalized)
    return {"ok": True, "steps": [{"nodeId": node["id"], "type": node["type"], "wouldExecute": True} for node in ordered]}

from __future__ import annotations

from workflows.workflow_parser import validate_workflow


def validate_workflow_execution(workflow: dict) -> dict:
    ok, message, normalized = validate_workflow(workflow)
    return {"ok": ok, "message": message, "workflow": normalized}

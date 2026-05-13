from __future__ import annotations

from datetime import datetime

from api.memory_storage import remember_event
from workflows.node_executor import execute_node
from workflows.workflow_parser import execution_order, validate_workflow


def execute_workflow_graph(payload: dict) -> dict:
    ok, message, workflow = validate_workflow(payload)
    if not ok:
        return {"ok": False, "error": message, "workflow": workflow}
    state = {"startedAt": datetime.now().isoformat(timespec="seconds"), "workflowId": workflow["id"]}
    steps = []
    failed = False
    try:
        ordered = execution_order(workflow)
    except Exception as error:
        return {"ok": False, "error": str(error), "workflow": workflow}
    for node in ordered:
        step = execute_node(node, state)
        steps.append(step)
        if not step.get("ok"):
            failed = True
            if not bool(node.get("continueOnError", False)):
                break
    result = {
        "ok": not failed,
        "workflow": workflow,
        "state": state,
        "steps": steps,
        "completedAt": datetime.now().isoformat(timespec="seconds"),
    }
    try:
        remember_event("workflow", f"Workflow {workflow['name']}", "completed" if result["ok"] else "failed", result)
    except OSError:
        pass
    return result

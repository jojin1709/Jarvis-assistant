from __future__ import annotations


def explain_workflow(workflow: dict) -> dict:
    return {
        "name": workflow.get("name") or workflow.get("id"),
        "nodes": len(workflow.get("nodes", [])),
        "edges": len(workflow.get("edges", [])),
        "reason": "Nodes execute in dependency order; failed nodes stop execution unless configured to continue.",
    }

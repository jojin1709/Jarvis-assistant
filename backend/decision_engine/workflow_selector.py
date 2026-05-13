from __future__ import annotations

from workflows.workflow_store import list_workflow_definitions


def select_workflow(goal: str) -> dict:
    workflows = list_workflow_definitions()
    tokens = {token.lower() for token in goal.split() if len(token) > 2}
    scored = []
    for workflow in workflows:
        text = f"{workflow.get('name', '')} {workflow.get('id', '')}".lower()
        score = sum(1 for token in tokens if token in text)
        if score:
            scored.append((score, workflow))
    if not scored:
        return {"workflow": None, "reason": "No saved workflow matched; use planner-generated graph."}
    scored.sort(key=lambda item: item[0], reverse=True)
    return {"workflow": scored[0][1], "reason": "Matched saved workflow by goal keywords."}

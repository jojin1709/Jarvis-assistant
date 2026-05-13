from __future__ import annotations

from workflows.workflow_store import list_workflow_definitions


def marketplace_workflows() -> dict:
    return {"local": list_workflow_definitions(), "remoteEnabled": False}

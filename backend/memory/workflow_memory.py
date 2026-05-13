from __future__ import annotations

from api.memory_storage import remember_event, search_memories


def remember_workflow_outcome(workflow_id: str, summary: str, metadata: dict | None = None) -> None:
    remember_event("workflows", f"Workflow {workflow_id}", summary, metadata or {})


def recall_workflows(query: str, limit: int = 8) -> list[dict]:
    return search_memories(query, limit=limit, kind="workflows")

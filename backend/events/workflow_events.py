from __future__ import annotations

from events.event_bus import emit_event


def workflow_started(workflow_id: str, payload: dict | None = None) -> dict:
    return emit_event("workflow_started", {"workflowId": workflow_id, **(payload or {})})


def workflow_completed(workflow_id: str, ok: bool, payload: dict | None = None) -> dict:
    return emit_event("workflow_completed" if ok else "workflow_failed", {"workflowId": workflow_id, **(payload or {})}, "success" if ok else "error")


def build_failed(payload: dict) -> dict:
    return emit_event("build_failed", payload, "error")


def security_alert(payload: dict) -> dict:
    return emit_event("security_alert", payload, "warning")

from __future__ import annotations

from recovery.rollback_manager import rollback_plan


def execute_recovery(snapshot_path: str, approved: bool = False) -> dict:
    plan = rollback_plan(snapshot_path)
    if not approved:
        return {**plan, "ok": False, "error": "Recovery execution requires explicit approval."}
    return {**plan, "ok": True, "message": "Recovery approval accepted. Manual restore hook is ready for controlled implementation."}

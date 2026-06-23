from __future__ import annotations

from persistence.workflow_recovery import recovery_candidates


def restore_readiness() -> dict:
    candidates = recovery_candidates()
    rollback: dict = {"available": False, "snapshots": []}
    try:
        from recovery.rollback_manager import rollback_status

        rollback = rollback_status()
        rollback["available"] = True
    except Exception as error:
        rollback["error"] = str(error)

    return {
        "recovery": candidates,
        "rollback": rollback,
        "recoverableCount": len(candidates) if isinstance(candidates, list) else 0,
    }

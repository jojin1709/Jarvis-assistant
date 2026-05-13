from __future__ import annotations

from persistence.workflow_recovery import recovery_candidates
from recovery.rollback_manager import rollback_status


def restore_readiness() -> dict:
    return {"recovery": recovery_candidates(), "rollback": rollback_status()}

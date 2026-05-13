from __future__ import annotations

from recovery.snapshot_engine import list_snapshots


def rollback_plan(snapshot_path: str) -> dict:
    return {
        "ok": True,
        "snapshot": snapshot_path,
        "requiresApproval": True,
        "steps": ["Review snapshot metadata", "Confirm affected paths", "Restore manually or through approved recovery executor"],
    }


def rollback_status() -> dict:
    return {"snapshots": list_snapshots(), "policy": "Rollback requires explicit user approval before filesystem changes."}

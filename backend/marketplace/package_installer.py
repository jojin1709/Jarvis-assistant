from __future__ import annotations


def installation_plan(package_ref: str) -> dict:
    return {"package": package_ref, "requiresApproval": True, "steps": ["Validate manifest", "Check signature/source", "Install into local marketplace cache"]}

from __future__ import annotations

from api.permissions import evaluate_permission, log_activity
from safety.policy import command_risk


def evaluate_action(action: str, label: str, command: str = "", path: str | None = None) -> dict:
    risk = command_risk(command) if command else {"allowed": True, "risk": "low", "reason": "No command supplied."}
    if not risk.get("allowed"):
        log_activity(f"Governance blocked: {label}", "error", "governance")
        return {"allowed": False, "requiresApproval": False, "reason": risk.get("reason"), "risk": risk.get("risk")}
    decision = evaluate_permission(action, label, path=path, command=command)
    return {"allowed": decision.allowed, "requiresApproval": decision.requires_confirmation, "reason": decision.message, "risk": decision.risk}

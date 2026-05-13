from __future__ import annotations

from safety.policy import command_risk


def preview_command(command: str) -> dict:
    risk = command_risk(command)
    return {"command": command, "risk": risk, "willExecute": False}

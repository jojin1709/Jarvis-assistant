from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from state_machine.execution_state import ExecutionState
from state_machine.transition_controller import can_transition


STATE_PATH = Path(__file__).resolve().parents[1] / "runtime" / "execution_state.json"


def current_state() -> dict:
    if not STATE_PATH.exists():
        return {"state": ExecutionState.IDLE.value, "updatedAt": datetime.now().isoformat(timespec="seconds"), "history": []}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"state": ExecutionState.IDLE.value, "updatedAt": datetime.now().isoformat(timespec="seconds"), "history": []}


def transition_to(target: str, reason: str = "") -> dict:
    state = current_state()
    current = state.get("state", ExecutionState.IDLE.value)
    if not can_transition(current, target):
        raise RuntimeError(f"Invalid execution transition: {current} -> {target}")
    entry = {"from": current, "to": target, "reason": reason, "createdAt": datetime.now().isoformat(timespec="seconds")}
    state["state"] = target
    state["updatedAt"] = entry["createdAt"]
    state.setdefault("history", []).append(entry)
    state["history"] = state["history"][-80:]
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state

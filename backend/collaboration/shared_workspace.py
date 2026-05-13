from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


COLLAB_PATH = Path(__file__).resolve().parents[1] / "runtime" / "collaboration.json"


def collaboration_state() -> dict:
    if not COLLAB_PATH.exists():
        return {"sessions": [], "sharedWorkflows": [], "updatedAt": datetime.now().isoformat(timespec="seconds")}
    try:
        return json.loads(COLLAB_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"sessions": [], "sharedWorkflows": [], "updatedAt": datetime.now().isoformat(timespec="seconds")}


def record_collaboration_event(kind: str, payload: dict) -> dict:
    state = collaboration_state()
    event = {"kind": kind, "payload": payload, "createdAt": datetime.now().isoformat(timespec="seconds")}
    state.setdefault("events", []).append(event)
    state["events"] = state["events"][-200:]
    state["updatedAt"] = event["createdAt"]
    COLLAB_PATH.parent.mkdir(parents=True, exist_ok=True)
    COLLAB_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return event

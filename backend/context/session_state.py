from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


SESSION_PATH = Path(__file__).resolve().parents[1] / "runtime" / "session_state.json"


def update_session(patch: dict) -> dict:
    state = session_state()
    state.update(patch)
    state["updatedAt"] = datetime.now().isoformat(timespec="seconds")
    SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    SESSION_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def session_state() -> dict:
    if not SESSION_PATH.exists():
        return {"createdAt": datetime.now().isoformat(timespec="seconds"), "activeGoal": "", "lastIntent": ""}
    try:
        return json.loads(SESSION_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"createdAt": datetime.now().isoformat(timespec="seconds"), "activeGoal": "", "lastIntent": ""}

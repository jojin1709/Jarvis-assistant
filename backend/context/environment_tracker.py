from __future__ import annotations

from context.environment_analyzer import environment_snapshot


def track_environment() -> dict:
    snapshot = environment_snapshot()
    readiness = {
        "docker": bool(snapshot.get("dockerAvailable")),
        "activeWindows": len(snapshot.get("activeWindows") or []),
        "cwd": snapshot.get("cwd", ""),
    }
    return {"snapshot": snapshot, "readiness": readiness}

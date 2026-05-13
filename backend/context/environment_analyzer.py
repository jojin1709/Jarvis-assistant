from __future__ import annotations

from desktop.window_manager import active_windows
from sandbox.executor import docker_available


def environment_snapshot() -> dict:
    import os
    import platform

    return {
        "os": platform.platform(),
        "cwd": os.getcwd(),
        "user": os.getenv("USERNAME") or os.getenv("USER") or "User",
        "dockerAvailable": docker_available(),
        "activeWindows": active_windows(limit=20),
    }

import os
import platform
import subprocess
from datetime import datetime

from api.browser_automation import browser_operator
from api.memory_storage import memory_storage_state, recent_memories
from terminal.service import terminal_service


def context_snapshot() -> dict:
    return {
        "capturedAt": datetime.now().isoformat(timespec="seconds"),
        "system": {
            "os": platform.platform(),
            "user": os.getenv("USERNAME") or os.getenv("USER") or "User",
            "cwd": os.getcwd(),
        },
        "processes": _running_processes(),
        "browser": browser_operator.state(),
        "terminal": {"jobs": terminal_service.history(limit=12)},
        "memory": memory_storage_state(),
        "recent": recent_memories(limit=8),
    }


def _running_processes() -> list[dict[str, str]]:
    if platform.system().lower() != "windows":
        return []
    try:
        result = subprocess.run(
            ["tasklist", "/fo", "csv", "/nh"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return []
    rows = []
    for line in result.stdout.splitlines()[:80]:
        parts = [part.strip('"') for part in line.split('","')]
        if len(parts) >= 2:
            rows.append({"name": parts[0], "pid": parts[1]})
    return rows

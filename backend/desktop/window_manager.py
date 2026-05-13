from __future__ import annotations

import platform
import subprocess


def active_windows(limit: int = 40) -> list[dict]:
    if platform.system().lower() != "windows":
        return []
    script = "Get-Process | Where-Object {$_.MainWindowTitle} | Select-Object -First %d Id,ProcessName,MainWindowTitle | ConvertTo-Json" % limit
    try:
        result = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True, timeout=5, check=False)
        import json

        data = json.loads(result.stdout or "[]")
        rows = data if isinstance(data, list) else [data]
        return [
            {"pid": row.get("Id"), "process": row.get("ProcessName"), "title": row.get("MainWindowTitle")}
            for row in rows
            if row.get("MainWindowTitle")
        ]
    except Exception:
        return []

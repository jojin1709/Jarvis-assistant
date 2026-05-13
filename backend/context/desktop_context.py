from __future__ import annotations

from desktop.automation import desktop_automation
from desktop.window_manager import active_windows


def desktop_context() -> dict:
    windows = active_windows()
    return {"automation": desktop_automation.status(), "windows": windows, "activeWindowCount": len(windows)}

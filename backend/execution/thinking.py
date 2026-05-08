from datetime import datetime
from threading import Lock


_lock = Lock()
_timeline: list[dict[str, str]] = []


def thinking_timeline() -> list[dict[str, str]]:
    with _lock:
        return list(reversed(_timeline[-120:]))


def reset_thinking(title: str | None = None) -> None:
    with _lock:
        _timeline.clear()
    if title:
        add_thinking_step("request", title, "running")


def add_thinking_step(phase: str, message: str, status: str = "info", tool: str | None = None) -> dict[str, str]:
    entry = {
        "id": f"think-{int(datetime.now().timestamp() * 1000)}-{len(_timeline) + 1}",
        "createdAt": datetime.now().isoformat(timespec="seconds"),
        "phase": phase,
        "status": status,
        "message": message,
        "tool": tool or "",
    }
    with _lock:
        _timeline.append(entry)
    return entry

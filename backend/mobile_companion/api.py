from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


NOTIFICATIONS_PATH = Path(__file__).resolve().parents[1] / "runtime" / "mobile_notifications.json"


def push_mobile_notification(title: str, body: str, level: str = "info", action: dict | None = None) -> dict:
    data = _load()
    item = {
        "id": f"mobile-{len(data) + 1}",
        "createdAt": datetime.now().isoformat(timespec="seconds"),
        "title": title,
        "body": body,
        "level": level,
        "action": action or {},
        "read": False,
    }
    data.append(item)
    _save(data[-200:])
    return item


def mobile_state() -> dict:
    return {"notifications": list(reversed(_load()[-80:])), "capabilities": ["monitor", "approve", "notify"]}


def _load() -> list[dict]:
    if not NOTIFICATIONS_PATH.exists():
        return []
    try:
        data = json.loads(NOTIFICATIONS_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(data: list[dict]) -> None:
    NOTIFICATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTIFICATIONS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

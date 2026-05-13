from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Callable


EVENT_PATH = Path(__file__).resolve().parents[1] / "runtime" / "events.jsonl"
_SUBSCRIBERS: dict[str, list[Callable[[dict], None]]] = {}


def emit_event(kind: str, payload: dict | None = None, level: str = "info") -> dict:
    event = {"id": f"evt-{datetime.now().strftime('%Y%m%d%H%M%S%f')}", "createdAt": datetime.now().isoformat(timespec="seconds"), "kind": kind, "level": level, "payload": payload or {}}
    EVENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EVENT_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    for handler in [*_SUBSCRIBERS.get(kind, []), *_SUBSCRIBERS.get("*", [])]:
        try:
            handler(event)
        except Exception:
            continue
    return event


def subscribe(kind: str, handler: Callable[[dict], None]) -> None:
    _SUBSCRIBERS.setdefault(kind, []).append(handler)


def recent_events(limit: int = 120) -> list[dict]:
    if not EVENT_PATH.exists():
        return []
    rows = []
    for line in EVENT_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(rows))

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


QUEUE_PATH = Path(__file__).resolve().parents[1] / "runtime" / "distributed_queue.json"


def enqueue_task(kind: str, payload: dict) -> dict:
    rows = _load()
    task = {"id": f"dist-{datetime.now().strftime('%Y%m%d%H%M%S%f')}", "kind": kind, "payload": payload, "status": "queued", "createdAt": datetime.now().isoformat(timespec="seconds")}
    rows.append(task)
    _save(rows)
    return task


def queue_state() -> dict:
    rows = _load()
    return {"queued": [row for row in rows if row.get("status") == "queued"], "all": rows[-100:]}


def _load() -> list[dict]:
    if not QUEUE_PATH.exists():
        return []
    try:
        data = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(rows: list[dict]) -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text(json.dumps(rows[-500:], indent=2), encoding="utf-8")

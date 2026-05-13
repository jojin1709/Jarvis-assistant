from __future__ import annotations

import json
from datetime import datetime

from app.config import BACKEND_DIR


WORKERS_PATH = BACKEND_DIR / "runtime" / "remote" / "workers.json"


def remote_workers() -> list[dict]:
    if not WORKERS_PATH.exists():
        return []
    try:
        data = json.loads(WORKERS_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def register_remote_worker(name: str, endpoint: str, scopes: list[str] | None = None) -> dict:
    workers = [worker for worker in remote_workers() if worker.get("name") != name]
    worker = {"name": name, "endpoint": endpoint, "scopes": scopes or [], "enabled": False, "registeredAt": datetime.now().isoformat(timespec="seconds")}
    workers.append(worker)
    WORKERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    WORKERS_PATH.write_text(json.dumps(workers, indent=2), encoding="utf-8")
    return worker

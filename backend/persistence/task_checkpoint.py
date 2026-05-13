from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


CHECKPOINT_DIR = Path(__file__).resolve().parents[1] / "runtime" / "checkpoints"


def save_checkpoint(task_id: str, state: dict) -> dict:
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"taskId": task_id, "savedAt": datetime.now().isoformat(timespec="seconds"), "state": state}
    path = CHECKPOINT_DIR / f"{task_id}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {"ok": True, "path": str(path), **payload}


def load_checkpoint(task_id: str) -> dict | None:
    path = CHECKPOINT_DIR / f"{task_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def latest_checkpoints(limit: int = 20) -> list[dict]:
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(CHECKPOINT_DIR.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)[:limit]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            rows.append({"taskId": data.get("taskId"), "savedAt": data.get("savedAt"), "path": str(path)})
        except Exception:
            continue
    return rows

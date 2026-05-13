from __future__ import annotations

import json
from datetime import datetime

from app.config import BACKEND_DIR


SCHEDULE_PATH = BACKEND_DIR / "runtime" / "sync" / "schedule.json"


def sync_schedule() -> dict:
    if not SCHEDULE_PATH.exists():
        return {"enabled": False, "intervalMinutes": 360, "lastRunAt": "", "nextRunAt": ""}
    try:
        data = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))
        return {"enabled": False, "intervalMinutes": 360, "lastRunAt": "", "nextRunAt": "", **data}
    except json.JSONDecodeError:
        return {"enabled": False, "intervalMinutes": 360, "lastRunAt": "", "nextRunAt": ""}


def update_sync_schedule(patch: dict) -> dict:
    schedule = sync_schedule()
    schedule.update({key: patch[key] for key in ("enabled", "intervalMinutes", "nextRunAt") if key in patch})
    schedule["updatedAt"] = datetime.now().isoformat(timespec="seconds")
    SCHEDULE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEDULE_PATH.write_text(json.dumps(schedule, indent=2), encoding="utf-8")
    return schedule

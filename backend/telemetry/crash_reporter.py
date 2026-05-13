from __future__ import annotations

import json
import traceback
from datetime import datetime

from app.config import BACKEND_DIR


CRASH_PATH = BACKEND_DIR / "runtime" / "telemetry" / "crashes.jsonl"


def record_crash(error: BaseException, context: dict | None = None) -> dict:
    entry = {
        "type": error.__class__.__name__,
        "message": str(error),
        "traceback": traceback.format_exception_only(error.__class__, error),
        "context": context or {},
        "createdAt": datetime.now().isoformat(timespec="seconds"),
    }
    CRASH_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CRASH_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def crash_summary(limit: int = 50) -> dict:
    if not CRASH_PATH.exists():
        return {"count": 0, "recent": []}
    rows = []
    for line in CRASH_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return {"count": len(rows), "recent": list(reversed(rows))}

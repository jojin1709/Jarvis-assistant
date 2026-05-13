from __future__ import annotations

import json
from datetime import datetime

from app.config import BACKEND_DIR


PROFILE_PATH = BACKEND_DIR / "runtime" / "optimization" / "execution_profiles.jsonl"


def record_profile(name: str, duration_ms: float, ok: bool, metadata: dict | None = None) -> dict:
    entry = {"name": name, "durationMs": round(duration_ms, 2), "ok": ok, "metadata": metadata or {}, "createdAt": _now()}
    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PROFILE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def profiler_summary(limit: int = 100) -> dict:
    entries = _entries(limit)
    if not entries:
        return {"count": 0, "averageMs": 0, "failureRate": 0, "recent": []}
    failures = [entry for entry in entries if not entry.get("ok")]
    average = sum(float(entry.get("durationMs", 0)) for entry in entries) / len(entries)
    return {"count": len(entries), "averageMs": round(average, 2), "failureRate": round(len(failures) / len(entries), 3), "recent": list(reversed(entries[-20:]))}


def _entries(limit: int) -> list[dict]:
    if not PROFILE_PATH.exists():
        return []
    rows = []
    for line in PROFILE_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


SNAPSHOT_DIR = Path(__file__).resolve().parents[1] / "runtime" / "snapshots"


def create_snapshot(label: str, paths: list[str] | None = None) -> dict:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"label": label, "createdAt": datetime.now().isoformat(timespec="seconds"), "paths": paths or []}
    path = SNAPSHOT_DIR / f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{_slug(label)}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {"ok": True, "snapshot": payload, "path": str(path)}


def list_snapshots(limit: int = 40) -> list[dict]:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    return [{"path": str(path), "name": path.name} for path in sorted(SNAPSHOT_DIR.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)[:limit]]


def _slug(value: str) -> str:
    import re

    return re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-") or "snapshot"

from __future__ import annotations

import json
from datetime import datetime

from app.config import BACKEND_DIR


SHARES_PATH = BACKEND_DIR / "runtime" / "community" / "shares.jsonl"


def export_share(kind: str, payload: dict) -> dict:
    entry = {"kind": kind, "payload": payload, "createdAt": datetime.now().isoformat(timespec="seconds"), "visibility": "local-export"}
    SHARES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SHARES_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {"ok": True, "share": entry}

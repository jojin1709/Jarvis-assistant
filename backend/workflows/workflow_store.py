from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from workflows.workflow_parser import normalize_workflow, validate_workflow


STORE_DIR = Path(__file__).resolve().parents[1] / "runtime" / "workflows"


def save_workflow_definition(payload: dict) -> dict:
    ok, message, workflow = validate_workflow(payload)
    if not ok:
        return {"ok": False, "error": message, "workflow": workflow}
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    workflow["updatedAt"] = datetime.now().isoformat(timespec="seconds")
    path = STORE_DIR / f"{workflow['id']}.json"
    path.write_text(json.dumps(workflow, indent=2), encoding="utf-8")
    return {"ok": True, "workflow": workflow, "path": str(path)}


def load_workflow_definition(workflow_id: str) -> dict | None:
    path = STORE_DIR / f"{workflow_id}.json"
    if not path.exists():
        return None
    return normalize_workflow(json.loads(path.read_text(encoding="utf-8")))


def list_workflow_definitions() -> list[dict]:
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(STORE_DIR.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            workflow = normalize_workflow(json.loads(path.read_text(encoding="utf-8")))
            rows.append({**workflow, "path": str(path)})
        except Exception:
            continue
    return rows

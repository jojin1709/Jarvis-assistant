import json
from datetime import datetime
from pathlib import Path
from threading import Lock

from api.memory_storage import configured_memory_root, remember_event


_lock = Lock()
_active = False
_current: dict | None = None
_last_saved: dict | None = None


def recorder_state() -> dict:
    with _lock:
        return {
            "active": _active,
            "current": _current,
            "lastSaved": _last_saved,
            "workflows": list_workflows(),
        }


def start_recording(name: str = "Jarvis workflow") -> dict:
    global _active, _current
    with _lock:
        _active = True
        _current = {
            "id": f"workflow-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "name": name.strip() or "Jarvis workflow",
            "startedAt": datetime.now().isoformat(timespec="seconds"),
            "actions": [],
        }
        return {"active": _active, "current": _current}


def stop_recording() -> dict:
    global _active, _current, _last_saved
    with _lock:
        if not _current:
            _active = False
            return {"active": False, "saved": None}

        workflow = {
            **_current,
            "endedAt": datetime.now().isoformat(timespec="seconds"),
            "actionCount": len(_current.get("actions", [])),
        }
        path = _workflow_dir() / f"{workflow['id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(workflow, indent=2), encoding="utf-8")
        remember_event(
            "workflows",
            workflow["name"],
            f"Recorded workflow with {workflow['actionCount']} action(s).",
            {"path": str(path), "workflow_id": workflow["id"]},
        )
        _last_saved = {**workflow, "path": str(path)}
        _current = None
        _active = False
        return {"active": False, "saved": _last_saved}


def record_action(kind: str, label: str, metadata: dict | None = None) -> None:
    with _lock:
        if not _active or not _current:
            return
        _current["actions"].append(
            {
                "id": f"action-{len(_current['actions']) + 1}",
                "kind": kind,
                "label": label,
                "metadata": metadata or {},
                "createdAt": datetime.now().isoformat(timespec="seconds"),
            }
        )


def list_workflows(limit: int = 20) -> list[dict]:
    folder = _workflow_dir()
    if not folder.exists():
        return []
    workflows = []
    for path in sorted(folder.glob("workflow-*.json"), key=lambda item: item.stat().st_mtime, reverse=True)[:limit]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        workflows.append(
            {
                "id": data.get("id") or path.stem,
                "name": data.get("name") or path.stem,
                "startedAt": data.get("startedAt", ""),
                "endedAt": data.get("endedAt", ""),
                "actionCount": len(data.get("actions", [])),
                "path": str(path),
            }
        )
    return workflows


def load_workflow(workflow_id: str) -> dict | None:
    candidate = _workflow_dir() / f"{workflow_id}.json"
    if not candidate.exists():
        return None
    try:
        return json.loads(candidate.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _workflow_dir() -> Path:
    return configured_memory_root() / "workflows" / "recordings"

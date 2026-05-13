from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


STATE_PATH = Path(__file__).resolve().parents[1] / "runtime" / "platform_state.json"
HISTORY_PATH = Path(__file__).resolve().parents[1] / "runtime" / "platform_history.jsonl"


def platform_state() -> dict:
    if not STATE_PATH.exists():
        return _default_state()
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return {**_default_state(), **data}
    except Exception:
        return _default_state()


def update_platform_state(patch: dict) -> dict:
    state = platform_state()
    state.update(patch)
    state["updatedAt"] = _now()
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def start_task(goal: str, graph: dict, strategy: dict, context_digest: dict) -> dict:
    state = platform_state()
    task_id = f"task-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    task = {
        "id": task_id,
        "goal": goal,
        "status": "running",
        "startedAt": _now(),
        "updatedAt": _now(),
        "graph": graph,
        "strategy": strategy,
        "contextDigest": context_digest,
        "steps": [],
        "failures": [],
    }
    state["activeTask"] = task
    state.setdefault("recentTasks", [])
    update_platform_state(state)
    append_history({"event": "task.started", "task": task})
    return task


def record_step(step: dict, ok: bool, message: str, data: dict | None = None) -> dict:
    state = platform_state()
    task = state.get("activeTask") or {}
    entry = {
        "createdAt": _now(),
        "step": step,
        "ok": ok,
        "message": message,
        "data": data or {},
    }
    task.setdefault("steps", []).append(entry)
    task["updatedAt"] = _now()
    if not ok:
        task.setdefault("failures", []).append(entry)
        state.setdefault("failureMemory", []).append({"goal": task.get("goal", ""), "step": step, "message": message, "createdAt": _now()})
        state["failureMemory"] = state["failureMemory"][-80:]
    state["activeTask"] = task
    update_platform_state(state)
    append_history({"event": "step.completed" if ok else "step.failed", "entry": entry, "taskId": task.get("id")})
    return entry


def finish_task(ok: bool, response: str, artifacts: dict) -> dict:
    state = platform_state()
    task = state.get("activeTask") or {}
    task["status"] = "completed" if ok else "failed"
    task["completedAt"] = _now()
    task["response"] = response
    task["artifactKeys"] = list(artifacts.keys())
    recent = [task, *state.get("recentTasks", [])]
    state["recentTasks"] = recent[:40]
    state["activeTask"] = None
    update_platform_state(state)
    append_history({"event": "task.finished", "task": task})
    return task


def append_history(event: dict) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"createdAt": _now(), **event}
    with HISTORY_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def platform_history(limit: int = 100) -> list[dict]:
    if not HISTORY_PATH.exists():
        return []
    rows = []
    for line in HISTORY_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(rows))


def _default_state() -> dict:
    return {
        "schemaVersion": 1,
        "updatedAt": _now(),
        "activeTask": None,
        "recentTasks": [],
        "failureMemory": [],
        "preferences": {},
    }


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")

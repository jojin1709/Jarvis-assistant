from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

from workflows.workflow_engine import execute_workflow_graph
from workflows.workflow_store import load_workflow_definition


SCHEDULE_PATH = Path(__file__).resolve().parents[1] / "runtime" / "scheduler.json"


class TaskScheduler:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started = False
        self._events: list[dict] = []

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._schedule_self_improvement()
        threading.Thread(target=self._loop, daemon=True).start()

    def list(self) -> dict:
        return {"tasks": _load(), "events": list(reversed(self._events[-80:])), "running": self._started}

    def upsert(self, task: dict) -> dict:
        tasks = _load()
        task = _normalize_task(task)
        tasks = [item for item in tasks if item["id"] != task["id"]]
        tasks.append(task)
        _save(tasks)
        return task

    def remove(self, task_id: str) -> bool:
        tasks = _load()
        next_tasks = [task for task in tasks if task["id"] != task_id]
        _save(next_tasks)
        return len(next_tasks) != len(tasks)

    def _loop(self) -> None:
        while True:
            now = datetime.now()
            tasks = _load()
            changed = False
            for task in tasks:
                if not task.get("enabled", True):
                    continue
                due_at = _parse_time(task.get("nextRunAt"))
                if due_at and due_at > now:
                    continue
                self._run_task(task)
                task["lastRunAt"] = now.isoformat(timespec="seconds")
                task["nextRunAt"] = (now + timedelta(seconds=max(30, int(task.get("intervalSeconds") or 3600)))).isoformat(timespec="seconds")
                changed = True
            if changed:
                _save(tasks)
            time.sleep(15)

    def _run_task(self, task: dict) -> None:
        if task.get("id") == "__self_improvement__":
            try:
                from self_improvement.engine import analyze_execution_quality

                result = analyze_execution_quality()
                self._events.append({"createdAt": _now(), "taskId": task["id"], "ok": True, "summary": result})
            except Exception as error:
                self._events.append({"createdAt": _now(), "taskId": task["id"], "ok": False, "error": str(error)})
            return

        workflow = load_workflow_definition(task.get("workflowId", ""))
        if not workflow:
            self._events.append({"createdAt": _now(), "taskId": task["id"], "ok": False, "error": "Workflow not found."})
            return
        result = execute_workflow_graph(workflow)
        self._events.append({"createdAt": _now(), "taskId": task["id"], "ok": result.get("ok"), "workflowId": workflow["id"]})

    def _schedule_self_improvement(self) -> None:
        tasks = _load()
        if any(task.get("id") == "__self_improvement__" for task in tasks):
            return
        self.upsert(
            {
                "id": "__self_improvement__",
                "name": "Daily self-improvement analysis",
                "goal": "analyze execution quality and record behavior patterns",
                "intervalSeconds": 86400,
                "nextRunAt": (datetime.now() + timedelta(hours=24)).isoformat(timespec="seconds"),
                "enabled": True,
            }
        )


def _normalize_task(task: dict) -> dict:
    task_id = str(task.get("id") or task.get("name") or f"task-{int(time.time())}").strip().replace(" ", "-").lower()
    return {
        "id": task_id,
        "name": str(task.get("name") or task_id),
        "workflowId": str(task.get("workflowId") or ""),
        "intervalSeconds": int(task.get("intervalSeconds") or 3600),
        "enabled": bool(task.get("enabled", True)),
        "nextRunAt": task.get("nextRunAt") or _now(),
        "lastRunAt": task.get("lastRunAt"),
    }


def _load() -> list[dict]:
    if not SCHEDULE_PATH.exists():
        return []
    try:
        data = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(tasks: list[dict]) -> None:
    SCHEDULE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEDULE_PATH.write_text(json.dumps(tasks, indent=2), encoding="utf-8")


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


scheduler = TaskScheduler()

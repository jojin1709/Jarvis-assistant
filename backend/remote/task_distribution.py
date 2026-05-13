from __future__ import annotations

from remote.remote_worker_manager import remote_workers


def distribution_plan(task: dict) -> dict:
    eligible = [worker for worker in remote_workers() if worker.get("enabled") and _matches(worker, task)]
    return {"mode": "local" if not eligible else "remote-ready", "eligibleWorkers": eligible, "task": task}


def _matches(worker: dict, task: dict) -> bool:
    scopes = set(worker.get("scopes") or [])
    return not scopes or str(task.get("scope") or "") in scopes

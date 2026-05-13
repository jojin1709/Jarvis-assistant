from __future__ import annotations

from distributed.distributed_queue import enqueue_task


def submit_remote_task(kind: str, payload: dict) -> dict:
    task = enqueue_task(kind, payload)
    return {"ok": True, "task": task, "message": "Task queued for remote/distributed execution adapter."}

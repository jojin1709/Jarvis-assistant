from __future__ import annotations

from distributed.remote_executor import submit_remote_task
from sandbox.executor import run_in_docker


def coordinate_execution(kind: str, payload: dict) -> dict:
    mode = payload.get("mode") or "local"
    if mode == "docker":
        return run_in_docker(str(payload.get("command") or ""), payload.get("workspace") or ".", image=payload.get("image") or "python:3.11-slim")
    if mode == "remote":
        return submit_remote_task(kind, payload)
    return {"ok": True, "mode": "local", "message": "Local execution should be handled by the relevant agent/service.", "payload": payload}

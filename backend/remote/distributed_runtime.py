from __future__ import annotations

from distributed.worker_manager import worker_status
from remote.remote_agents import remote_agent_status


def distributed_runtime_status() -> dict:
    return {"local": worker_status(), "remote": remote_agent_status()}

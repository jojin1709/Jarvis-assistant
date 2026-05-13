from __future__ import annotations

from remote.remote_worker_manager import remote_workers


def remote_agent_status() -> dict:
    return {"enabled": False, "agents": [], "workers": remote_workers()}

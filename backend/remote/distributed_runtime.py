from __future__ import annotations


def distributed_runtime_status() -> dict:
    worker_info: dict = {"workers": [], "online": 0}
    remote_info: dict = {"agents": [], "connected": False}

    try:
        from distributed.worker_manager import worker_status

        worker_info = worker_status()
    except Exception as error:
        worker_info["error"] = str(error)

    try:
        from remote.remote_agents import remote_agent_status

        remote_info = remote_agent_status()
    except Exception as error:
        remote_info["error"] = str(error)

    return {"local": worker_info, "remote": remote_info, "enabled": False}

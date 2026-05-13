from __future__ import annotations

from distributed.distributed_queue import queue_state
from sandbox.executor import docker_available


def worker_status() -> dict:
    return {"local": {"available": True}, "docker": {"available": docker_available()}, "remote": {"available": False, "message": "Remote workers are configured through queue adapters."}, "queue": queue_state()}

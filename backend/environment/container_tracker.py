from __future__ import annotations

from devops.service_manager import docker_status


def container_state() -> dict:
    return docker_status()

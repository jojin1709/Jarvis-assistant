from __future__ import annotations

from terminal.service import terminal_service


def run_deployment_check(command: str, cwd: str | None = None) -> dict:
    job = terminal_service.run_sync(command, cwd=cwd, timeout=240)
    return job.as_dict()

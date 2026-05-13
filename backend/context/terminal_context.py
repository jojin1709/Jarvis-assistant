from __future__ import annotations

from terminal.service import terminal_service


def terminal_context(limit: int = 20) -> dict:
    jobs = terminal_service.history(limit=limit)
    failures = [job for job in jobs if job.get("status") not in {"completed", "queued", "running"}]
    return {"jobs": jobs, "failures": failures, "running": [job for job in jobs if job.get("status") == "running"]}

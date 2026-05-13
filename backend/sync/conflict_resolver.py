from __future__ import annotations

from datetime import datetime


def resolve_conflict(local_meta: dict, remote_meta: dict, strategy: str = "newest") -> dict:
    if strategy == "local":
        winner = "local"
    elif strategy == "remote":
        winner = "remote"
    else:
        local_time = _parse(local_meta.get("updatedAt"))
        remote_time = _parse(remote_meta.get("updatedAt"))
        winner = "remote" if remote_time > local_time else "local"
    return {"winner": winner, "strategy": strategy, "local": local_meta, "remote": remote_meta}


def _parse(value: str | None) -> datetime:
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.min

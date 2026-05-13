from __future__ import annotations

from datetime import datetime


_POOL: dict[str, dict] = {}


def acquire_browser(provider: str = "default", profile: str = "default") -> dict:
    key = f"{provider}:{profile}"
    entry = _POOL.get(key) or {"key": key, "provider": provider, "profile": profile, "createdAt": _now(), "leases": 0}
    entry["leases"] += 1
    entry["lastUsedAt"] = _now()
    _POOL[key] = entry
    return entry


def release_browser(key: str) -> dict:
    entry = _POOL.get(key)
    if not entry:
        return {"ok": False, "message": "Browser lease not found."}
    entry["leases"] = max(0, int(entry.get("leases", 0)) - 1)
    entry["lastReleasedAt"] = _now()
    return {"ok": True, "entry": entry}


def browser_pool_status() -> dict:
    return {"count": len(_POOL), "instances": list(_POOL.values())}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")

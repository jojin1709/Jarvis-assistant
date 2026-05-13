from __future__ import annotations

import gc

try:
    import psutil
except Exception:  # pragma: no cover
    psutil = None


def memory_pressure() -> dict:
    if not psutil:
        return {"available": False, "pressure": "unknown", "percent": 0}
    memory = psutil.virtual_memory()
    pressure = "critical" if memory.percent >= 90 else "high" if memory.percent >= 78 else "normal"
    return {"available": True, "pressure": pressure, "percent": memory.percent, "availableMb": round(memory.available / 1024 / 1024)}


def optimize_memory() -> dict:
    before = memory_pressure()
    collected = gc.collect()
    after = memory_pressure()
    return {"ok": True, "collected": collected, "before": before, "after": after}

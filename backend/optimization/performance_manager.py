from __future__ import annotations

import psutil

from optimization.resource_optimizer import resource_plan


def performance_status() -> dict:
    plan = resource_plan()
    cpu_percent = psutil.cpu_percent(interval=0.2)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    mode = "conservative" if plan["maxParallelTasks"] == 1 else "balanced"
    if cpu_percent > 80 or memory.percent > 85:
        mode = "throttled"

    return {
        "ok": True,
        "plan": plan,
        "mode": mode,
        "cpu": {"percent": cpu_percent, "cores": psutil.cpu_count(logical=True)},
        "memory": {
            "percent": memory.percent,
            "availableMb": memory.available // (1024 * 1024),
            "totalMb": memory.total // (1024 * 1024),
        },
        "disk": {"percent": disk.percent, "freeGb": round(disk.free / (1024**3), 1)},
    }

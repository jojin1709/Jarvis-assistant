from __future__ import annotations

import shutil


def system_metrics() -> dict:
    try:
        import psutil

        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        return {
            "cpuPercent": psutil.cpu_percent(interval=0.1),
            "cpuCount": psutil.cpu_count(logical=True),
            "ram": {"total": memory.total, "available": memory.available, "percent": memory.percent},
            "disk": {"total": disk.total, "free": disk.free, "percent": disk.percent},
            "source": "psutil",
        }
    except Exception as error:
        disk = shutil.disk_usage(".")
        return {
            "cpuPercent": None,
            "cpuCount": None,
            "ram": {"total": None, "available": None, "percent": None},
            "disk": {"total": disk.total, "free": disk.free, "percent": round((1 - disk.free / disk.total) * 100, 1)},
            "source": "stdlib",
            "warning": str(error),
        }

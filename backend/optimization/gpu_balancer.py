from __future__ import annotations

from environment.gpu_monitor import gpu_status


def gpu_allocation(requests: list[dict] | None = None) -> dict:
    status = gpu_status()
    gpus = status.get("gpus") or []
    if not gpus:
        return {"available": False, "assignments": [], "status": status}
    assignments = []
    for index, request in enumerate(requests or []):
        gpu = gpus[index % len(gpus)]
        assignments.append({"task": request.get("id") or f"task-{index}", "gpu": gpu.get("index", index), "model": request.get("model", "local")})
    return {"available": True, "assignments": assignments, "status": status}

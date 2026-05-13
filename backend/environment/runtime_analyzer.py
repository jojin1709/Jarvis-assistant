from __future__ import annotations

from environment.container_tracker import container_state
from environment.gpu_monitor import gpu_metrics
from environment.network_monitor import network_state
from environment.process_tracker import running_processes
from environment.system_monitor import system_metrics


def runtime_analysis() -> dict:
    system = system_metrics()
    gpu = gpu_metrics()
    network = network_state()
    containers = container_state()
    processes = running_processes(limit=80)
    pressure = _pressure(system)
    return {
        "system": system,
        "gpu": gpu,
        "network": network,
        "containers": containers,
        "processes": processes,
        "pressure": pressure,
        "recommendations": _recommendations(pressure, network, containers),
    }


def _pressure(system: dict) -> dict:
    cpu = system.get("cpuPercent") or 0
    ram = (system.get("ram") or {}).get("percent") or 0
    disk = (system.get("disk") or {}).get("percent") or 0
    return {"cpu": cpu, "ram": ram, "disk": disk, "high": cpu > 85 or ram > 88 or disk > 92}


def _recommendations(pressure: dict, network: dict, containers: dict) -> list[str]:
    rows = []
    if pressure.get("high"):
        rows.append("Reduce parallel execution and prefer queued workflows until resource pressure drops.")
    if not network.get("online"):
        rows.append("Prefer offline/local workflows and postpone internet research or provider calls.")
    if not containers.get("available"):
        rows.append("Docker sandbox unavailable; avoid untrusted generated code execution.")
    return rows

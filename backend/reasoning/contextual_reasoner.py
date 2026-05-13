from __future__ import annotations


def analyze_context(goal: str, context: dict) -> dict:
    world = context.get("world", {}) if isinstance(context, dict) else {}
    signals = []
    constraints = []
    if world.get("browser", {}).get("status") == "running":
        signals.append("Browser automation is already running.")
        constraints.append("Avoid starting a second browser workflow.")
    running_jobs = [job for job in world.get("terminal", {}).get("jobs", []) if job.get("status") in {"queued", "running"}]
    if running_jobs:
        signals.append(f"{len(running_jobs)} terminal job(s) still active.")
    if not world.get("desktop", {}).get("available", False):
        constraints.append("Desktop automation dependency is unavailable.")
    if "docker" in goal.lower() and not world.get("environment", {}).get("dockerAvailable"):
        constraints.append("Docker is not available; use local checks or request installation.")
    return {"signals": signals, "constraints": constraints, "risk": "medium" if constraints else "low"}

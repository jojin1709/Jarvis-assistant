from __future__ import annotations

from environment.runtime_analyzer import runtime_analysis


def resource_plan() -> dict:
    analysis = runtime_analysis()
    high = analysis.get("pressure", {}).get("high")
    return {"analysis": analysis, "maxParallelTasks": 1 if high else 3, "preferLocalModels": not analysis.get("network", {}).get("online", True)}

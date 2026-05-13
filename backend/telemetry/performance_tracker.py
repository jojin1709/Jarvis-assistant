from __future__ import annotations

from environment.runtime_analyzer import runtime_analysis
from optimization.performance_manager import performance_status


def performance_snapshot() -> dict:
    return {"runtime": runtime_analysis(), "optimization": performance_status()}

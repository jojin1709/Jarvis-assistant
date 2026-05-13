from __future__ import annotations

from environment.runtime_analyzer import runtime_analysis
from setup.dependency_manager import detect_dependency_managers


def runtime_setup_plan(path: str) -> dict:
    return {"runtime": runtime_analysis(), "dependencies": detect_dependency_managers(path)}

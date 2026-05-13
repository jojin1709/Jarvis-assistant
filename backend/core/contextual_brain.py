from __future__ import annotations

from environment.runtime_analyzer import runtime_analysis
from memory.context_retriever import retrieve_context_for_goal
from platform_core.intelligence import build_intelligence_snapshot


def build_contextual_brain(goal: str, include_vision: bool = False) -> dict:
    intelligence = build_intelligence_snapshot(goal, include_vision=include_vision)
    return {
        "intelligence": intelligence,
        "runtime": runtime_analysis(),
        "memory": retrieve_context_for_goal(goal),
    }

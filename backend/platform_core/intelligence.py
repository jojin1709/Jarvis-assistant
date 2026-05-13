from __future__ import annotations

from context.context_manager import multimodal_context
from decision_engine.strategy_selector import choose_strategy
from learning.behavior import learning_state
from memory.context_retriever import retrieve_context_for_goal
from platform_core.service_catalog import catalog_snapshot, tools_for_goal
from platform_core.state_store import platform_history, platform_state


def build_intelligence_snapshot(goal: str = "", include_vision: bool = False) -> dict:
    context = multimodal_context(goal=goal, include_vision=include_vision)
    state = platform_state()
    strategy = choose_strategy(goal, context.get("world", {})) if goal else {}
    learning = learning_state()
    return {
        "goal": goal,
        "context": context,
        "strategy": strategy,
        "availableServices": catalog_snapshot(),
        "recommendedTools": tools_for_goal(goal) if goal else [],
        "platformState": state,
        "history": platform_history(limit=30),
        "learning": {"preferences": learning.get("preferences", {}), "eventCount": len(learning.get("events", []))},
        "memoryContext": retrieve_context_for_goal(goal) if goal else {},
    }

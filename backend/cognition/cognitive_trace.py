from __future__ import annotations

from cognition.execution_memory import execution_memory
from cognition.reasoning_timeline import reasoning_timeline
from cognition.strategy_history import strategy_history


def cognitive_trace() -> dict:
    return {"reasoning": reasoning_timeline(), "execution": execution_memory(), "strategies": strategy_history()}

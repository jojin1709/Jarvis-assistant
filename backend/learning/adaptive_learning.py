from __future__ import annotations

from learning.execution_optimizer import preferred_tools
from learning.strategy_memory import strategy_preferences


def adaptive_learning_state() -> dict:
    return {"preferredTools": preferred_tools(), "preferredStrategies": strategy_preferences()}

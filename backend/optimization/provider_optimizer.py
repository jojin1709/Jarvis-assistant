from __future__ import annotations

from decision_engine.provider_selector import select_provider
from optimization.resource_optimizer import resource_plan


def optimized_provider(task_type: str, context: dict | None = None) -> dict:
    plan = resource_plan()
    if plan.get("preferLocalModels"):
        return {"provider": "ollama", "source": "local", "reason": "Network unavailable or constrained; prefer local provider."}
    return select_provider(task_type, context or {})

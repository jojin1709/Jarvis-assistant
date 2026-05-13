from __future__ import annotations

from decision_engine.agent_router import route_step


def route_tasks(steps: list[dict]) -> list[dict]:
    return [{**step, "route": route_step(step)} for step in steps]

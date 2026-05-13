from __future__ import annotations

from context.multimodal_reasoner import reason_over_context
from context.world_state import build_world_state


def multimodal_context(goal: str = "", include_vision: bool = False) -> dict:
    world = build_world_state(include_vision=include_vision)
    reasoning = reason_over_context(goal, world) if goal else {}
    return {"world": world, "reasoning": reasoning}

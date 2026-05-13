from __future__ import annotations

from reasoning.chain_of_thought import build_reasoning_trace
from reasoning.contextual_reasoner import analyze_context
from reasoning.strategy_generator import generate_strategies
from reasoning.task_decomposer import decompose_goal


def build_cognitive_plan(goal: str, intelligence: dict) -> dict:
    context = intelligence.get("context") or {}
    strategies = generate_strategies(goal, intelligence)
    selected = max(strategies, key=lambda strategy: strategy.get("confidence", 0.0)) if strategies else {}
    return {
        "goal": goal,
        "contextAnalysis": analyze_context(goal, context),
        "taskGraph": decompose_goal(goal),
        "strategies": strategies,
        "selectedStrategy": selected,
        "reasoningTrace": build_reasoning_trace(goal, context, strategies),
    }

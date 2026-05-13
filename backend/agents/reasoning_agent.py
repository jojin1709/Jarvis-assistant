from __future__ import annotations

from agents.base import AgentResult, BaseAgent
from planner.engine import PlanStep, TaskState
from reasoning.planning_engine import build_cognitive_plan


class ReasoningAgent(BaseAgent):
    name = "reasoning"

    def run(self, step: PlanStep, state: TaskState) -> AgentResult:
        intelligence = state.artifacts.get("intelligence") or {}
        plan = build_cognitive_plan(state.graph.goal, intelligence)
        state.artifacts["cognitivePlan"] = plan
        return AgentResult(True, f"Reasoned plan ready with {plan.get('taskGraph', {}).get('stepCount', 0)} step(s).", plan)

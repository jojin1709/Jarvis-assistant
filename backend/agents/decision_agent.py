from __future__ import annotations

from agents.base import AgentResult, BaseAgent
from decision_engine.adaptive_decision_system import decide_next_action
from planner.engine import PlanStep, TaskState


class DecisionAgent(BaseAgent):
    name = "decision"

    def run(self, step: PlanStep, state: TaskState) -> AgentResult:
        intelligence = state.artifacts.get("intelligence") or {}
        plan = intelligence.get("cognitivePlan") or {}
        review = state.artifacts.get("reflection", {}).get("review") or {}
        decision = decide_next_action(state.graph.goal, plan, review=review)
        state.artifacts["decision"] = decision
        return AgentResult(not decision.get("stop"), decision.get("reason", "Decision complete."), decision)

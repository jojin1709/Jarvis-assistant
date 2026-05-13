from __future__ import annotations

from agents.base import AgentResult, BaseAgent
from planner.engine import PlanStep, TaskState
from reflection.execution_reviewer import review_execution
from reflection.strategy_optimizer import optimize_strategy


class ReflectionAgent(BaseAgent):
    name = "reflection"

    def run(self, step: PlanStep, state: TaskState) -> AgentResult:
        payload = {"result": {"graph": state.graph.as_dict(), "logs": state.logs, "artifacts": state.artifacts}}
        review = review_execution(payload)
        optimized = optimize_strategy((state.artifacts.get("intelligence") or {}).get("cognitivePlan") or {}, review)
        state.artifacts["reflection"] = {"review": review, "optimized": optimized}
        return AgentResult(True, review.get("summary", "Reflection complete."), state.artifacts["reflection"])

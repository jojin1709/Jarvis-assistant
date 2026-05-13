from agents.base import AgentResult, BaseAgent
from planner.engine import PlanStep, TaskState


class PlannerAgent(BaseAgent):
    name = "planner"

    def run(self, step: PlanStep, state: TaskState) -> AgentResult:
        state.log(f"Planner selected tool: {step.tool}")
        return AgentResult(True, "Plan classified and ready.", {"graph": state.graph.as_dict()})

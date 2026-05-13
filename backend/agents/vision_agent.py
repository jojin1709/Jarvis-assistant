from __future__ import annotations

from agents.base import AgentResult, BaseAgent
from planner.engine import PlanStep, TaskState
from vision.screenshot import capture_screen


class VisionAgent(BaseAgent):
    name = "vision"

    def run(self, step: PlanStep, state: TaskState) -> AgentResult:
        result = capture_screen()
        state.artifacts["vision"] = result
        return AgentResult(bool(result.get("ok")), result.get("summary") or result.get("error") or "Vision analysis complete.", result)

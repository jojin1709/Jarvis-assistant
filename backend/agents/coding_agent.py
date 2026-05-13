from pathlib import Path

from agents.base import AgentResult, BaseAgent
from coding.fullstack import create_mern_restaurant_project
from coding.self_heal import run_self_healing_loop
from planner.engine import PlanStep, TaskState


class CodingAgent(BaseAgent):
    name = "coding"

    def run(self, step: PlanStep, state: TaskState) -> AgentResult:
        if step.tool == "create_fullstack_project":
            result = create_mern_restaurant_project(state.graph.goal)
            if result.get("ok"):
                state.artifacts["project"] = result
                return AgentResult(True, f"Created project at {result['path']}", result)
            return AgentResult(False, str(result.get("error") or "Project creation failed."), result)

        if step.tool == "self_heal":
            project = state.artifacts.get("project") or {}
            path = project.get("path")
            if not path:
                return AgentResult(False, "No project path is available for self-healing.")
            result = run_self_healing_loop(Path(path), install=False, max_attempts=step.max_attempts)
            state.artifacts["verification"] = result
            return AgentResult(bool(result.get("ok")), "Self-healing verification complete." if result.get("ok") else "Self-healing could not fully repair the project.", result)

        return AgentResult(False, f"CodingAgent does not support tool {step.tool}.")

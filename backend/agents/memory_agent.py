from agents.base import AgentResult, BaseAgent
from api.memory_storage import remember_event, remember_project
from planner.engine import PlanStep, TaskState


class MemoryAgent(BaseAgent):
    name = "memory"

    def run(self, step: PlanStep, state: TaskState) -> AgentResult:
        if step.tool == "remember_project":
            project = state.artifacts.get("project") or {}
            if project.get("path"):
                remember_project(str(project.get("name") or "Generated project"), str(project["path"]), state.graph.goal)
                return AgentResult(True, "Project stored in Jarvis memory.", project)
        remember_event("automation", state.graph.goal[:180], "\n".join(item.get("message", "") for item in state.logs), {"artifacts": state.artifacts})
        return AgentResult(True, "Execution summary stored in Jarvis memory.", {"artifactKeys": list(state.artifacts.keys())})

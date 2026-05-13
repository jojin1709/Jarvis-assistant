from agents.base import AgentResult, BaseAgent
from api.browser_automation import browser_operator
from planner.engine import PlanStep, TaskState


class BrowserAgent(BaseAgent):
    name = "browser"

    def run(self, step: PlanStep, state: TaskState) -> AgentResult:
        if step.tool == "open_preview":
            project = state.artifacts.get("project") or {}
            url = str(project.get("previewUrl") or "http://127.0.0.1:5173")
            result = browser_operator.run_async(f"open {url}")
            return AgentResult(bool(result.get("accepted", True)), result.get("response", "Preview requested."), result)
        result = browser_operator.run_async(step.goal)
        return AgentResult(bool(result.get("accepted", True)), result.get("response", "Browser task requested."), result)

from __future__ import annotations

from agents.base import AgentResult, BaseAgent
from desktop.automation import desktop_automation
from desktop.clipboard import read_clipboard, write_clipboard
from desktop.window_manager import active_windows
from planner.engine import PlanStep, TaskState


class DesktopAgent(BaseAgent):
    name = "desktop"

    def run(self, step: PlanStep, state: TaskState) -> AgentResult:
        lowered = step.goal.lower()
        if step.tool == "desktop_state":
            data = {"automation": desktop_automation.status(), "windows": active_windows()}
            state.artifacts["desktop"] = data
            return AgentResult(True, f"Desktop state captured: {len(data['windows'])} active window(s).", data)
        if step.tool == "clipboard_read":
            data = read_clipboard()
            return AgentResult(bool(data.get("ok")), "Clipboard read." if data.get("ok") else data.get("error", "Clipboard unavailable."), data)
        if step.tool == "clipboard_write":
            text = state.artifacts.get("lastText") or step.goal
            data = write_clipboard(str(text))
            return AgentResult(bool(data.get("ok")), data.get("message") or data.get("error", "Clipboard action complete."), data)
        if "click" in lowered:
            result = desktop_automation.click()
            return AgentResult(result.ok, result.message, result.as_dict())
        return AgentResult(True, "Desktop action analyzed. Use explicit mouse/keyboard commands for direct control.", {"windows": active_windows()})

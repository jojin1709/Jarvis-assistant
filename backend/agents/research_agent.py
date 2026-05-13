from __future__ import annotations

from agents.base import AgentResult, BaseAgent
from planner.engine import PlanStep, TaskState
from research.search_engine import web_search
from research.summarizer import summarize_text


class ResearchAgent(BaseAgent):
    name = "research"

    def run(self, step: PlanStep, state: TaskState) -> AgentResult:
        result = web_search(state.graph.goal)
        summary = summarize_text(" ".join(item.get("title", "") for item in result.get("results", [])))
        payload = {**result, "summary": summary}
        state.artifacts["research"] = payload
        return AgentResult(bool(result.get("ok")), summary.get("summary") or result.get("error") or "Research complete.", payload)

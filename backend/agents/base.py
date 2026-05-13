from __future__ import annotations

from dataclasses import dataclass

from planner.engine import PlanStep, TaskState


@dataclass
class AgentResult:
    ok: bool
    message: str
    data: dict | None = None


class BaseAgent:
    name = "base"

    def run(self, step: PlanStep, state: TaskState) -> AgentResult:
        raise NotImplementedError

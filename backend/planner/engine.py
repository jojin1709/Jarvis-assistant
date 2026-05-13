from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


AgentName = Literal["planner", "reasoning", "coding", "browser", "desktop", "vision", "research", "recon", "report", "memory", "devops", "workflow", "reflection", "decision"]


@dataclass
class PlanStep:
    id: str
    goal: str
    agent: AgentName
    tool: str
    depends_on: list[str] = field(default_factory=list)
    risk: str = "low"
    status: str = "pending"
    attempts: int = 0
    max_attempts: int = 2
    result: str = ""


@dataclass
class TaskGraph:
    goal: str
    created_at: str
    steps: list[PlanStep]

    def ready_steps(self) -> list[PlanStep]:
        completed = {step.id for step in self.steps if step.status == "completed"}
        return [
            step
            for step in self.steps
            if step.status == "pending" and all(dep in completed for dep in step.depends_on)
        ]

    def as_dict(self) -> dict:
        return {
            "goal": self.goal,
            "createdAt": self.created_at,
            "steps": [step.__dict__ for step in self.steps],
        }


@dataclass
class TaskState:
    graph: TaskGraph
    logs: list[dict[str, str]] = field(default_factory=list)
    artifacts: dict[str, object] = field(default_factory=dict)

    def log(self, message: str, level: str = "info") -> None:
        self.logs.append(
            {
                "createdAt": datetime.now().isoformat(timespec="seconds"),
                "level": level,
                "message": message,
            }
        )


def build_task_graph(goal: str) -> TaskGraph:
    normalized = " ".join(goal.lower().strip().split())
    steps: list[PlanStep]

    if _is_bug_bounty_goal(normalized):
        steps = [
            PlanStep("scope", "Normalize target scope and create recon workspace", "recon", "scope", risk="low"),
            PlanStep("recon", "Run available recon tool chain", "recon", "bug_bounty_recon", depends_on=["scope"], risk="medium"),
            PlanStep("analyze", "Analyze recon output for likely vulnerabilities and anomalies", "recon", "analyze_findings", depends_on=["recon"], risk="low"),
            PlanStep("report", "Generate structured vulnerability report", "report", "markdown_report", depends_on=["analyze"], risk="low"),
            PlanStep("memory", "Store target findings and report in memory", "memory", "remember_findings", depends_on=["report"], risk="low"),
        ]
    elif _is_workflow_goal(normalized):
        steps = [
            PlanStep("workflow", "Select or create reusable workflow graph", "workflow", "create_basic_workflow" if "create" in normalized else "list_workflows", risk="low"),
            PlanStep("memory", "Store workflow orchestration summary", "memory", "remember_execution", depends_on=["workflow"], risk="low"),
        ]
    elif _is_full_stack_goal(normalized):
        steps = [
            PlanStep("workspace", "Create full-stack project workspace", "coding", "create_fullstack_project", risk="medium"),
            PlanStep("install", "Install project dependencies", "devops", "install_dependencies", depends_on=["workspace"], risk="medium"),
            PlanStep("verify", "Run build and health checks", "devops", "verify_build", depends_on=["install"], risk="medium"),
            PlanStep("heal", "Patch detected build/runtime errors and retry", "coding", "self_heal", depends_on=["verify"], risk="medium", max_attempts=3),
            PlanStep("preview", "Launch browser preview for the working project", "browser", "open_preview", depends_on=["heal"], risk="low"),
            PlanStep("memory", "Store project summary and execution history", "memory", "remember_project", depends_on=["preview"], risk="low"),
        ]
    elif _is_research_goal(normalized):
        steps = [
            PlanStep("research", "Search and summarize technical information", "research", "internet_research", risk="low"),
            PlanStep("memory", "Store research summary", "memory", "remember_execution", depends_on=["research"], risk="low"),
        ]
    elif _is_vision_goal(normalized):
        steps = [
            PlanStep("vision", "Capture and reason over the visible desktop state", "vision", "screen_understanding", risk="low"),
            PlanStep("desktop", "Analyze active desktop windows and available desktop actions", "desktop", "desktop_state", depends_on=["vision"], risk="low"),
            PlanStep("execute", goal, "devops", "general_execute", depends_on=["desktop"], risk="medium"),
            PlanStep("memory", "Store visual execution summary", "memory", "remember_execution", depends_on=["execute"], risk="low"),
        ]
    elif _is_desktop_goal(normalized):
        steps = [
            PlanStep("desktop", "Inspect and operate desktop state", "desktop", "desktop_state", risk="medium"),
            PlanStep("memory", "Store desktop automation summary", "memory", "remember_execution", depends_on=["desktop"], risk="low"),
        ]
    elif _is_devops_goal(normalized):
        steps = [
            PlanStep("environment", "Inspect local DevOps environment and services", "devops", "environment_report", risk="low"),
            PlanStep("memory", "Store DevOps operation summary", "memory", "remember_execution", depends_on=["environment"], risk="low"),
        ]
    else:
        steps = [
            PlanStep("plan", "Classify user goal and select best tool", "planner", "classify", risk="low"),
            PlanStep("execute", goal, "devops", "general_execute", depends_on=["plan"], risk="medium"),
            PlanStep("memory", "Store execution summary", "memory", "remember_execution", depends_on=["execute"], risk="low"),
        ]

    return TaskGraph(goal=goal, created_at=datetime.now().isoformat(timespec="seconds"), steps=steps)


def _is_full_stack_goal(normalized: str) -> bool:
    full_stack_terms = ("mern", "full stack", "full-stack", "react and node", "express", "mongodb")
    build_terms = ("build", "create", "generate", "make", "develop")
    return any(term in normalized for term in full_stack_terms) and any(term in normalized for term in build_terms)


def _is_bug_bounty_goal(normalized: str) -> bool:
    return any(term in normalized for term in ("bug bounty", "find bugs", "recon", "vulnerability", "vulnerabilities", "scan target"))


def _is_workflow_goal(normalized: str) -> bool:
    return "workflow" in normalized or "automation pipeline" in normalized


def _is_research_goal(normalized: str) -> bool:
    return any(term in normalized for term in ("research", "search docs", "stackoverflow", "github issue", "summarize article"))


def _is_vision_goal(normalized: str) -> bool:
    return any(term in normalized for term in ("screen", "screenshot", "what do you see", "click the", "visible", "window"))


def _is_desktop_goal(normalized: str) -> bool:
    return any(term in normalized for term in ("desktop", "clipboard", "mouse", "keyboard", "active window"))


def _is_devops_goal(normalized: str) -> bool:
    return any(term in normalized for term in ("docker", "deploy", "service", "environment", "logs", "restart"))

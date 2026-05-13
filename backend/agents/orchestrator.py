from __future__ import annotations

from agents.base import AgentResult
from agents.browser_agent import BrowserAgent
from agents.coding_agent import CodingAgent
from agents.decision_agent import DecisionAgent
from agents.desktop_agent import DesktopAgent
from agents.devops_agent import DevOpsAgent
from agents.memory_agent import MemoryAgent
from agents.message_bus import message_bus
from agents.planner_agent import PlannerAgent
from agents.recon_agent import ReconAgent
from agents.reflection_agent import ReflectionAgent
from agents.report_agent import ReportAgent
from agents.research_agent import ResearchAgent
from agents.reasoning_agent import ReasoningAgent
from agents.vision_agent import VisionAgent
from agents.workflow_agent import WorkflowAgent
from decision_engine.retry_planner import plan_retry
from learning.behavior import record_behavior
from planner.engine import PlanStep, TaskState, build_task_graph
from platform_core.state_store import finish_task, record_step, start_task


AGENTS = {
    "planner": PlannerAgent(),
    "reasoning": ReasoningAgent(),
    "decision": DecisionAgent(),
    "coding": CodingAgent(),
    "browser": BrowserAgent(),
    "desktop": DesktopAgent(),
    "vision": VisionAgent(),
    "research": ResearchAgent(),
    "recon": ReconAgent(),
    "reflection": ReflectionAgent(),
    "report": ReportAgent(),
    "memory": MemoryAgent(),
    "devops": DevOpsAgent(),
    "workflow": WorkflowAgent(),
}


def execute_autonomous_goal(goal: str, intelligence: dict | None = None) -> dict:
    state = TaskState(build_task_graph(goal))
    state.artifacts["intelligence"] = intelligence or {}
    state.log(f"Autonomous goal received: {goal}", "info")
    message_bus.publish("orchestrator", "planner", "goal.received", {"goal": goal})
    platform_task = start_task(
        goal,
        state.graph.as_dict(),
        (intelligence or {}).get("strategy", {}),
        _context_digest((intelligence or {}).get("context", {})),
    )

    while True:
        ready = state.graph.ready_steps()
        if not ready:
            break
        for step in ready:
            _run_step(step, state)

    failed = [step for step in state.graph.steps if step.status == "failed"]
    response_lines = [step.result for step in state.graph.steps if step.result]
    response = "\n".join(response_lines) or "Autonomous task complete."
    finish_task(not failed, response, state.artifacts)
    record_behavior("task_type", (intelligence or {}).get("strategy", {}).get("taskType", "general"), "success" if not failed else "failure", {"taskId": platform_task["id"]})
    return {
        "ok": not failed,
        "response": response,
        "graph": state.graph.as_dict(),
        "logs": state.logs,
        "artifacts": state.artifacts,
        "platformTask": platform_task,
    }


def _run_step(step: PlanStep, state: TaskState) -> None:
    agent = AGENTS.get(step.agent)
    if not agent:
        step.status = "failed"
        step.result = f"No agent registered for {step.agent}."
        state.log(step.result, "error")
        return

    step.status = "running"
    while step.attempts < step.max_attempts:
        step.attempts += 1
        state.log(f"{step.agent} running {step.tool}: {step.goal}", "running")
        message_bus.publish("orchestrator", step.agent, "step.started", {"step": step.__dict__})
        result: AgentResult = agent.run(step, state)
        step.result = result.message
        if result.ok:
            step.status = "completed"
            state.log(result.message, "success")
            message_bus.publish(step.agent, "orchestrator", "step.completed", {"step": step.__dict__, "result": result.message})
            record_step(step.__dict__, True, result.message, result.data)
            if result.data is not None:
                state.artifacts[step.id] = result.data
            return
        state.log(result.message, "error")
        message_bus.publish(step.agent, "orchestrator", "step.failed", {"step": step.__dict__, "result": result.message})
        retry = plan_retry(result.message, step.attempts)
        state.artifacts.setdefault("retryPlans", {})[step.id] = retry
        record_step(step.__dict__, False, result.message, {"retry": retry, "data": result.data or {}})
        if retry.get("strategy") == "self_heal" and step.agent != "coding":
            state.artifacts.setdefault("repairHints", []).append({"step": step.id, "message": result.message})
        if step.attempts >= step.max_attempts:
            break
    step.status = "failed"


def _context_digest(context: dict) -> dict:
    world = context.get("world", {}) if isinstance(context, dict) else {}
    return {
        "browserUrl": world.get("browser", {}).get("currentUrl", ""),
        "terminalJobs": len(world.get("terminal", {}).get("jobs") or []),
        "dockerAvailable": world.get("environment", {}).get("dockerAvailable"),
        "memoryReady": world.get("memory", {}).get("initialized"),
    }

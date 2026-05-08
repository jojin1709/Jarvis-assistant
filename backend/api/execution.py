from datetime import datetime

from agents.task_planner import build_execution_plan
from api.ai_provider import ask_ai
from api.memory_storage import remember_event
from automation.workflow_recorder import record_action
from execution.control import checkpoint, reset_execution_control
from execution.thinking import add_thinking_step, reset_thinking
from execution.verification import can_retry, looks_failed, verification_label
from tools.app_launcher import launch_from_command
from tools.automation_tool import run_automation_command
from tools.browser_tool import run_browser_command
from tools.code_generator import run_code_generation
from tools.file_tool import run_file_command
from tools.memory_tool import run_memory_command
from tools.terminal_tool import run_terminal_tool
from tools.website_generator import run_website_generation


_logs: list[dict[str, str]] = []


def execution_logs() -> list[dict[str, str]]:
    return list(reversed(_logs[-120:]))


def add_log(message: str, level: str = "info") -> dict[str, str]:
    entry = {
        "id": f"log-{len(_logs) + 1}",
        "createdAt": datetime.now().isoformat(timespec="seconds"),
        "level": level,
        "message": message,
    }
    _logs.append(entry)
    return entry


def preview_execution_plan(text: str) -> dict[str, object]:
    command = " ".join(text.strip().split())
    if not command:
        return {"plan": [], "response": "Tell me what to plan."}
    reset_thinking(f"Understanding request: {command}")
    add_thinking_step("planning", "Building a multi-step execution plan.", "running", "task_planner")
    plan_steps = build_execution_plan(command)
    add_thinking_step("planning", f"Plan contains {len(plan_steps)} step(s).", "success", "task_planner")
    return {
        "response": f"Plan ready with {len(plan_steps)} step(s).",
        "plan": [{"label": step.label, "tool": step.tool_hint, "risk": step.risk} for step in plan_steps],
    }


def execute_agent_task(text: str) -> dict[str, object]:
    command = " ".join(text.strip().split())
    if not command:
        return {"response": "Tell me what to execute.", "logs": execution_logs()}

    reset_execution_control()
    reset_thinking(f"Understanding request: {command}")
    add_log(f"Task received: {command}", "info")
    add_thinking_step("planning", "Creating a task plan before execution.", "running", "task_planner")
    plan_steps = build_execution_plan(command)
    plan = [step.label for step in plan_steps]
    add_log(f"Plan created with {len(plan)} step(s).", "success")
    add_thinking_step("planning", f"Plan created with {len(plan)} step(s).", "success", "task_planner")

    results: list[str] = []
    for step in plan_steps:
        checkpoint()
        label = step.label.strip()
        if not label:
            continue
        add_log(f"Running: {label} [{step.tool_hint}, {step.risk} risk]", "running")
        add_thinking_step("execution", f"Running: {label}", "running", step.tool_hint)
        record_action("agent_step", label, {"tool": step.tool_hint, "risk": step.risk})
        result = _run_step(label)
        if looks_failed(result) and can_retry(label, result):
            add_log(f"Retrying after verification issue: {label}", "warning")
            add_thinking_step("retry", f"Retrying: {label}", "warning", step.tool_hint)
            result = _run_step(label)
        results.append(result)
        status = "success" if not looks_failed(result) else "error"
        add_log(f"{verification_label(result)}: {result}", status)
        add_thinking_step("verification", f"{verification_label(result)}: {result}", status, step.tool_hint)

    response = "\n".join(results) if results else "No executable steps were found."
    remember_event(
        "workflows",
        command[:180],
        response,
        {"plan": [{"label": step.label, "tool": step.tool_hint, "risk": step.risk} for step in plan_steps]},
    )
    return {
        "response": response,
        "plan": [{"label": step.label, "tool": step.tool_hint, "risk": step.risk} for step in plan_steps],
        "logs": execution_logs(),
    }


def _run_step(step: str) -> str:
    for runner in (
        run_memory_command,
        run_website_generation,
        run_code_generation,
        run_file_command,
        run_browser_command,
        launch_from_command,
        run_automation_command,
        run_terminal_tool,
    ):
        result = runner(step)
        if result:
            return result

    add_log("No direct tool matched. Asking AI for concise execution guidance.", "info")
    return ask_ai(
        "The user asked Jarvis to execute this task, but no local tool matched. "
        "Reply with one concise next action, not a tutorial.\n\n"
        f"Task: {step}"
    )

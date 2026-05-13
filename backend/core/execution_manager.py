from __future__ import annotations

from events.event_dispatcher import dispatch
from governance.safety_governor import evaluate_action
from persistence.task_checkpoint import save_checkpoint
from platform_core.cognitive_loop import run_cognitive_execution_loop
from state_machine.execution_state import ExecutionState
from state_machine.workflow_state_manager import current_state, transition_to


def execute_with_controls(goal: str, brain: dict, cognitive_plan: dict) -> dict:
    safety = evaluate_action("automation.run", f"autonomous platform goal: {goal}")
    if not safety.get("allowed") or safety.get("requiresApproval"):
        dispatch("security_alert", {"goal": goal, "safety": safety}, "warning")
        return {"ok": False, "response": safety.get("reason", "Execution blocked by governance."), "safety": safety}

    _safe_transition(ExecutionState.PLANNING.value, "Cognitive plan ready.")
    checkpoint = save_checkpoint(f"core-{abs(hash(goal))}", {"goal": goal, "brain": _light_brain(brain), "plan": cognitive_plan})
    dispatch("task_checkpointed", checkpoint)
    _safe_transition(ExecutionState.EXECUTING.value, "Starting cognitive execution loop.")
    result = run_cognitive_execution_loop(goal, brain.get("intelligence") or {})
    _safe_transition(ExecutionState.COMPLETED.value if result.get("ok") else ExecutionState.FAILED.value, result.get("response", "Execution finished."))
    dispatch("workflow_completed" if result.get("ok") else "workflow_failed", {"goal": goal, "ok": result.get("ok"), "review": result.get("review")}, "success" if result.get("ok") else "error")
    return result


def _light_brain(brain: dict) -> dict:
    return {
        "runtimePressure": brain.get("runtime", {}).get("pressure", {}),
        "memoryCount": brain.get("memory", {}).get("memoryCount", 0),
        "knowledgeCount": brain.get("memory", {}).get("knowledgeCount", 0),
    }


def _safe_transition(target: str, reason: str) -> None:
    try:
        transition_to(target, reason)
    except RuntimeError:
        state = current_state().get("state")
        if state in {ExecutionState.COMPLETED.value, ExecutionState.FAILED.value}:
            transition_to(ExecutionState.IDLE.value, "Resetting completed state for new run.")
            transition_to(target, reason)
        else:
            raise

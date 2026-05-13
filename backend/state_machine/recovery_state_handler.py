from __future__ import annotations

from state_machine.execution_state import ExecutionState
from state_machine.workflow_state_manager import current_state, transition_to


def enter_recovery(reason: str) -> dict:
    state = current_state()
    if state.get("state") != ExecutionState.RECOVERING.value:
        return transition_to(ExecutionState.RECOVERING.value, reason)
    return state

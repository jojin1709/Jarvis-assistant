from __future__ import annotations

from state_machine.execution_state import ExecutionState


ALLOWED_TRANSITIONS = {
    ExecutionState.IDLE: {ExecutionState.PLANNING, ExecutionState.RECOVERING},
    ExecutionState.PLANNING: {ExecutionState.EXECUTING, ExecutionState.WAITING, ExecutionState.FAILED},
    ExecutionState.EXECUTING: {ExecutionState.OBSERVING, ExecutionState.RETRYING, ExecutionState.COMPLETED, ExecutionState.FAILED},
    ExecutionState.OBSERVING: {ExecutionState.REFLECTING, ExecutionState.EXECUTING, ExecutionState.FAILED},
    ExecutionState.REFLECTING: {ExecutionState.RETRYING, ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.WAITING},
    ExecutionState.RETRYING: {ExecutionState.EXECUTING, ExecutionState.FAILED},
    ExecutionState.WAITING: {ExecutionState.EXECUTING, ExecutionState.RECOVERING, ExecutionState.FAILED},
    ExecutionState.RECOVERING: {ExecutionState.PLANNING, ExecutionState.EXECUTING, ExecutionState.FAILED},
    ExecutionState.COMPLETED: {ExecutionState.IDLE},
    ExecutionState.FAILED: {ExecutionState.IDLE, ExecutionState.RECOVERING},
}


def can_transition(current: str, target: str) -> bool:
    current_state = ExecutionState(current)
    target_state = ExecutionState(target)
    return target_state in ALLOWED_TRANSITIONS[current_state]

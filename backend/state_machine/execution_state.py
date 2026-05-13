from __future__ import annotations

from enum import StrEnum


class ExecutionState(StrEnum):
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    OBSERVING = "OBSERVING"
    REFLECTING = "REFLECTING"
    RETRYING = "RETRYING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RECOVERING = "RECOVERING"

FAILURE_MARKERS = (
    "failed",
    "not found",
    "blocked",
    "could not",
    "error",
    "not detected",
    "attempted",
    "confirmation required",
    "denied",
)

RETRYABLE_MARKERS = (
    "timeout",
    "connection",
    "not detected",
    "service error",
    "try again",
)

NON_RETRYABLE_MARKERS = (
    "confirmation required",
    "blocked",
    "denied",
    "delete",
    "remove",
    "shutdown",
    "restart",
)


def looks_failed(result: str) -> bool:
    lowered = result.lower()
    return any(marker in lowered for marker in FAILURE_MARKERS)


def can_retry(step: str, result: str) -> bool:
    lowered_step = step.lower()
    lowered_result = result.lower()
    if any(marker in lowered_step or marker in lowered_result for marker in NON_RETRYABLE_MARKERS):
        return False
    return any(marker in lowered_result for marker in RETRYABLE_MARKERS)


def verification_label(result: str) -> str:
    if looks_failed(result):
        return "Verification failed"
    if "opened successfully" in result.lower() or "complete" in result.lower() or "created" in result.lower():
        return "Verified"
    return "Completed"

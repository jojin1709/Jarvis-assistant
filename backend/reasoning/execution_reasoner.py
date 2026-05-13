from __future__ import annotations

from decision_engine.retry_planner import plan_retry


def observe_result(step: dict, result: dict | str) -> dict:
    text = result if isinstance(result, str) else str(result.get("message") or result.get("error") or result)
    ok = not _looks_failed(text)
    return {"stepId": step.get("id"), "ok": ok, "observation": text[:800], "retry": plan_retry(text, int(step.get("attempts") or 1))}


def should_continue(observations: list[dict], max_failures: int = 3) -> dict:
    failures = [item for item in observations if not item.get("ok")]
    if len(failures) >= max_failures:
        return {"continue": False, "reason": "Failure threshold reached."}
    blocking = [item for item in failures if item.get("retry", {}).get("strategy") == "request_approval"]
    if blocking:
        return {"continue": False, "reason": "Human approval is required before continuing."}
    return {"continue": True, "reason": "Execution can continue."}


def _looks_failed(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in ("failed", "error", "traceback", "blocked", "denied", "exception"))

from __future__ import annotations


def verify_execution_result(result: dict) -> dict:
    ok = bool(result.get("ok"))
    response = str(result.get("response") or result.get("result", {}).get("response") or "")
    failed_markers = ("failed", "traceback", "blocked", "denied", "exception")
    has_failure_text = any(marker in response.lower() for marker in failed_markers)
    return {"ok": ok and not has_failure_text, "hasFailureText": has_failure_text, "responseLength": len(response)}

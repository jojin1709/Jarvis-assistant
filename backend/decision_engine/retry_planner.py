from __future__ import annotations


def plan_retry(error_text: str, attempt: int = 1) -> dict:
    lowered = (error_text or "").lower()
    if any(marker in lowered for marker in ("rate limit", "429", "quota")):
        return {"retry": True, "delaySeconds": min(300, 30 * attempt), "strategy": "provider_fallback"}
    if any(marker in lowered for marker in ("timeout", "connection", "network")):
        return {"retry": True, "delaySeconds": min(120, 10 * attempt), "strategy": "network_retry"}
    if any(marker in lowered for marker in ("traceback", "syntaxerror", "build failed", "cannot find module")):
        return {"retry": True, "delaySeconds": 0, "strategy": "self_heal"}
    if any(marker in lowered for marker in ("permission", "confirmation", "protected")):
        return {"retry": False, "delaySeconds": 0, "strategy": "request_approval"}
    return {"retry": attempt < 2, "delaySeconds": 5, "strategy": "single_retry"}

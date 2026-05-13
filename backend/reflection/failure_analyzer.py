from __future__ import annotations


def analyze_failure(message: str, context: dict | None = None) -> dict:
    lowered = (message or "").lower()
    if any(token in lowered for token in ("syntaxerror", "traceback", "cannot find module", "build failed")):
        category = "code_or_build"
        advice = "Route to coding self-heal and rerun verification."
    elif any(token in lowered for token in ("timeout", "network", "connection")):
        category = "environment_or_network"
        advice = "Retry with backoff or switch provider/tool."
    elif any(token in lowered for token in ("permission", "approval", "protected", "denied")):
        category = "safety_gate"
        advice = "Stop autonomous continuation and request approval."
    elif any(token in lowered for token in ("login", "auth", "captcha")):
        category = "manual_session"
        advice = "Pause and request manual session restoration."
    else:
        category = "unknown"
        advice = "Collect more observations before retrying."
    return {"category": category, "advice": advice, "message": message[:1000], "contextKeys": list((context or {}).keys())}

from __future__ import annotations


def reason_about_screen(analysis: dict) -> dict:
    detected_text = str(analysis.get("ocr", {}).get("text") or "")
    ui = analysis.get("ui", {})
    popups = ui.get("popups") or []
    elements = ui.get("elements") or []
    source = analysis.get("source") or "screen"
    brightness = analysis.get("brightness")

    observations = []
    risks = []
    next_actions = []

    if detected_text:
        observations.append(f"OCR detected {min(len(detected_text.split()), 999)} word(s).")
    if popups:
        labels = ", ".join(item.get("label", "") for item in popups[:4])
        observations.append(f"Possible popup/dialog language detected: {labels}.")
        risks.append("Visible blocking dialog may require user confirmation or error handling.")
    if elements:
        observations.append(f"Detected {len(elements)} actionable UI text hint(s).")
    if brightness is not None:
        observations.append("Screen is dim." if brightness < 75 else "Screen is bright." if brightness > 180 else "Screen brightness is balanced.")

    lowered = detected_text.lower()
    if any(marker in lowered for marker in ("traceback", "exception", "failed", "error")):
        next_actions.append("Capture the visible error text and route it to the self-healing/debugging loop.")
    if any(marker in lowered for marker in ("sign in", "log in", "password")):
        next_actions.append("Pause automation and request manual login; credentials must not be automated or stored.")
    if not next_actions and elements:
        next_actions.append("Use detected UI hints to choose a stable click/type target.")
    if not next_actions:
        next_actions.append("Refresh context after the next browser, terminal, or desktop action.")

    return {
        "summary": f"Analyzed {source}: " + " ".join(observations or ["no strong visual signals detected."]),
        "observations": observations,
        "risks": risks,
        "nextActions": next_actions,
    }

from __future__ import annotations

import json
from datetime import datetime

from app.config import BACKEND_DIR


CONSENT_PATH = BACKEND_DIR / "runtime" / "legal" / "consents.json"


DEFAULT_CONSENTS = {
    "cloudSync": False,
    "telemetry": False,
    "browserAutomation": False,
    "desktopAutomation": False,
    "pluginExecution": False,
    "securityTooling": False,
}


def consent_state() -> dict:
    if not CONSENT_PATH.exists():
        return {"consents": DEFAULT_CONSENTS, "updatedAt": ""}
    try:
        data = json.loads(CONSENT_PATH.read_text(encoding="utf-8"))
        return {"consents": {**DEFAULT_CONSENTS, **data.get("consents", {})}, "updatedAt": data.get("updatedAt", "")}
    except json.JSONDecodeError:
        return {"consents": DEFAULT_CONSENTS, "updatedAt": ""}


def update_consents(patch: dict) -> dict:
    state = consent_state()
    state["consents"].update({key: bool(value) for key, value in patch.items() if key in DEFAULT_CONSENTS})
    state["updatedAt"] = datetime.now().isoformat(timespec="seconds")
    CONSENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONSENT_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state

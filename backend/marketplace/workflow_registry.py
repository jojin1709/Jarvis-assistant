from __future__ import annotations

import os

from workflows.workflow_store import list_workflow_definitions


REMOTE_MARKETPLACE_URL = os.getenv("JX_JARVIS_MARKETPLACE_URL", "").strip().rstrip("/")


def marketplace_workflows() -> dict:
    local = list_workflow_definitions()
    remote_enabled = bool(REMOTE_MARKETPLACE_URL)
    remote: list[dict] = []

    if remote_enabled:
        try:
            from providers.http_client import json_get

            data = json_get(f"{REMOTE_MARKETPLACE_URL}/workflows", timeout=5)
            remote = data.get("workflows", []) if isinstance(data, dict) else []
        except Exception:
            remote = []

    return {
        "local": local,
        "remote": remote,
        "remoteEnabled": remote_enabled,
        "remoteUrl": REMOTE_MARKETPLACE_URL,
    }

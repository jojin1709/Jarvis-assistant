from __future__ import annotations

from marketplace.workflow_registry import marketplace_workflows


def public_workflows() -> dict:
    return {"enabled": False, "source": "local-registry", "workflows": marketplace_workflows()}

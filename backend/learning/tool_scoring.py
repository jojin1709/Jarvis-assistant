from __future__ import annotations

from learning.behavior import learning_state, record_behavior


def record_tool_result(tool: str, ok: bool, metadata: dict | None = None) -> dict:
    return record_behavior("tool", tool, "success" if ok else "failure", metadata or {})


def tool_scores() -> list[dict]:
    return learning_state().get("preferences", {}).get("tool", [])

from __future__ import annotations

from learning.tool_scoring import tool_scores


def preferred_tools(limit: int = 8) -> list[dict]:
    scores = tool_scores()
    if scores:
        return scores[:limit]

    return [
        {"tool": "browser", "score": 0, "uses": 0, "hint": "No usage data yet"},
        {"tool": "terminal", "score": 0, "uses": 0, "hint": "No usage data yet"},
        {"tool": "file_manager", "score": 0, "uses": 0, "hint": "No usage data yet"},
    ][:limit]

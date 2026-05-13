from __future__ import annotations

from learning.tool_scoring import tool_scores


def preferred_tools(limit: int = 8) -> list[dict]:
    return tool_scores()[:limit]

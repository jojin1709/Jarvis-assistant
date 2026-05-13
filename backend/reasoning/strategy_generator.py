from __future__ import annotations

from platform_core.service_catalog import tools_for_goal


def generate_strategies(goal: str, intelligence: dict) -> list[dict]:
    tools = tools_for_goal(goal)
    failures = (intelligence.get("platformState") or {}).get("failureMemory") or []
    strategies = []
    if "coding" in tools:
        strategies.append({"id": "engineer_debug_loop", "agents": ["coding", "devops", "browser", "memory"], "confidence": 0.84})
    if "recon" in tools:
        strategies.append({"id": "security_recon_report", "agents": ["recon", "research", "report", "memory"], "confidence": 0.81})
    if "desktop" in tools or "vision" in tools:
        strategies.append({"id": "vision_desktop_operator", "agents": ["vision", "desktop", "browser", "memory"], "confidence": 0.76})
    if "research" in tools:
        strategies.append({"id": "research_synthesis", "agents": ["research", "memory", "report"], "confidence": 0.78})
    strategies.append({"id": "general_safe_execution", "agents": tools, "confidence": 0.62})
    if failures:
        for strategy in strategies:
            strategy["priorFailureCount"] = len(failures)
            strategy["confidence"] = round(max(0.35, strategy["confidence"] - min(len(failures), 5) * 0.03), 2)
    return strategies

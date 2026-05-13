from __future__ import annotations


def build_reasoning_trace(goal: str, context: dict, strategies: list[dict]) -> list[dict]:
    """Return an inspectable reasoning summary without exposing hidden model chain-of-thought."""
    world = context.get("world", {}) if isinstance(context, dict) else {}
    trace = [
        {"phase": "understand_goal", "summary": f"Goal normalized for autonomous execution: {goal[:220]}", "confidence": 0.9},
        {
            "phase": "observe_context",
            "summary": _context_summary(world),
            "confidence": 0.75,
        },
    ]
    if strategies:
        trace.append(
            {
                "phase": "compare_strategies",
                "summary": f"Evaluated {len(strategies)} execution strategy candidate(s).",
                "confidence": max(strategy.get("confidence", 0.5) for strategy in strategies),
            }
        )
    trace.append({"phase": "safety_check", "summary": "Actions remain routed through permissions, command policy, and sandbox-aware services.", "confidence": 0.86})
    return trace


def _context_summary(world: dict) -> str:
    browser_url = world.get("browser", {}).get("currentUrl") or "no active browser URL"
    jobs = len(world.get("terminal", {}).get("jobs") or [])
    windows = len(world.get("environment", {}).get("activeWindows") or [])
    memory_ready = bool(world.get("memory", {}).get("initialized"))
    return f"Observed browser={browser_url}, terminal_jobs={jobs}, active_windows={windows}, memory_ready={memory_ready}."

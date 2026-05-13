from __future__ import annotations

from decision_engine.strategy_selector import choose_strategy


def reason_over_context(goal: str, world_state: dict) -> dict:
    strategy = choose_strategy(goal, world_state)
    signals = []
    browser = world_state.get("browser", {})
    if browser.get("currentUrl"):
        signals.append(f"Browser active at {browser.get('currentUrl')}")
    terminal_jobs = world_state.get("terminal", {}).get("jobs") or []
    running = [job for job in terminal_jobs if job.get("status") in {"running", "queued"}]
    if running:
        signals.append(f"{len(running)} terminal job(s) still active")
    vision = world_state.get("vision") or {}
    if vision.get("summary"):
        signals.append(vision["summary"])
    return {"goal": goal, "strategy": strategy, "signals": signals, "confidence": 0.82 if signals else 0.64}

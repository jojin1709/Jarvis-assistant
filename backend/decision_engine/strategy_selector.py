from __future__ import annotations

from decision_engine.provider_selector import select_provider
from decision_engine.retry_planner import plan_retry


def choose_strategy(goal: str, world_state: dict | None = None) -> dict:
    lowered = goal.lower()
    if any(token in lowered for token in ("build", "code", "fix", "bug", "repo")):
        task_type = "coding"
        workflow = "coding_self_heal"
    elif any(token in lowered for token in ("research", "search", "docs", "github")):
        task_type = "research"
        workflow = "research_pipeline"
    elif any(token in lowered for token in ("screen", "click", "window", "desktop")):
        task_type = "automation"
        workflow = "desktop_vision_operator"
    elif any(token in lowered for token in ("recon", "vulnerability", "bug bounty")):
        task_type = "research"
        workflow = "bug_bounty_recon"
    else:
        task_type = "chat"
        workflow = "general_assistant"
    return {
        "taskType": task_type,
        "workflow": workflow,
        "provider": select_provider(task_type, world_state),
        "retry": plan_retry("", 0),
    }

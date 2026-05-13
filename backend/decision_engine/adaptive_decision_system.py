from __future__ import annotations

from decision_engine.execution_scorer import score_execution_plan
from decision_engine.workflow_selector import select_workflow
from reflection.strategy_optimizer import optimize_strategy


def decide_next_action(goal: str, cognitive_plan: dict, review: dict | None = None) -> dict:
    workflow = select_workflow(goal)
    score = score_execution_plan(cognitive_plan)
    optimized = optimize_strategy(cognitive_plan, review or {}) if review else {"strategy": cognitive_plan.get("selectedStrategy", {}), "adaptations": []}
    stop = bool(optimized.get("strategy", {}).get("requiresApproval"))
    return {
        "workflowSelection": workflow,
        "planScore": score,
        "strategy": optimized.get("strategy", {}),
        "adaptations": optimized.get("adaptations", []),
        "stop": stop,
        "reason": "Approval required." if stop else "Continue with selected strategy.",
    }

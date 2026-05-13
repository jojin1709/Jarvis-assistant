from __future__ import annotations

from agents.orchestrator import execute_autonomous_goal
from decision_engine.adaptive_decision_system import decide_next_action
from memory.context_retriever import retrieve_context_for_goal
from orchestration.coordination_manager import coordinate_goal
from reasoning.planning_engine import build_cognitive_plan
from reflection.execution_reviewer import review_execution
from reflection.learning_engine import learn_from_execution


def run_cognitive_execution_loop(goal: str, intelligence: dict, max_cycles: int = 2) -> dict:
    memory_context = retrieve_context_for_goal(goal)
    cognitive_plan = build_cognitive_plan(goal, {**intelligence, "memoryContext": memory_context})
    coordination = coordinate_goal(goal, cognitive_plan)

    cycles = []
    current_intelligence = {**intelligence, "cognitivePlan": cognitive_plan, "memoryContext": memory_context, "coordination": coordination}
    final_result = None
    final_review = None
    decision = decide_next_action(goal, cognitive_plan)

    for cycle in range(1, max_cycles + 1):
        if decision.get("stop"):
            break
        result = execute_autonomous_goal(goal, intelligence=current_intelligence)
        review = review_execution(result)
        learning = learn_from_execution(goal, review, cognitive_plan.get("selectedStrategy"))
        decision = decide_next_action(goal, cognitive_plan, review=review)
        cycles.append({"cycle": cycle, "result": result, "review": review, "decision": decision, "learning": learning})
        final_result = result
        final_review = review
        if result.get("ok") or not _should_retry(decision, review, cycle, max_cycles):
            break
        current_intelligence = {
            **current_intelligence,
            "previousReview": review,
            "adaptedStrategy": decision.get("strategy", {}),
            "adaptations": decision.get("adaptations", []),
        }

    ok = bool(final_result and final_result.get("ok"))
    response = str((final_result or {}).get("response") or decision.get("reason") or "Autonomous cognitive execution finished.")
    return {
        "ok": ok,
        "goal": goal,
        "response": response,
        "cognitivePlan": cognitive_plan,
        "coordination": coordination,
        "cycles": cycles,
        "review": final_review or {},
        "result": final_result or {"ok": False, "response": decision.get("reason", "Execution stopped before starting.")},
        "decision": decision,
    }


def _should_retry(decision: dict, review: dict, cycle: int, max_cycles: int) -> bool:
    if cycle >= max_cycles:
        return False
    if decision.get("stop"):
        return False
    if review.get("score", 0) >= 70 and not review.get("failedSteps"):
        return False
    categories = {item.get("category") for item in review.get("failureAnalysis", [])}
    return bool(categories & {"code_or_build", "environment_or_network", "unknown"})

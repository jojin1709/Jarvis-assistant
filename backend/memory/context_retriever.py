from __future__ import annotations

from memory.semantic_memory import semantic_recall


def retrieve_context_for_goal(goal: str) -> dict:
    recall = semantic_recall(goal, limit=6)
    return {
        "goal": goal,
        "memoryCount": len(recall.get("memories", [])),
        "knowledgeCount": len(recall.get("knowledge", [])),
        "items": recall,
    }

from __future__ import annotations

from api.permissions import permission_activity
from execution.thinking import thinking_timeline
from knowledge.vector_store import knowledge_stats
from learning.behavior import learning_state
from self_improvement.engine import analyze_execution_quality


def telemetry_snapshot() -> dict:
    learning = learning_state()
    quality = analyze_execution_quality()
    return {
        "thinking": thinking_timeline()[-80:],
        "security": permission_activity()[:80],
        "knowledge": knowledge_stats(),
        "learning": {"preferences": learning.get("preferences", {}), "eventCount": len(learning.get("events", []))},
        "quality": quality,
    }

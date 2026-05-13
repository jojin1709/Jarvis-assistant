from __future__ import annotations

from events.event_bus import recent_events
from optimization.execution_profiler import profiler_summary


def execution_metrics() -> dict:
    events = recent_events(200)
    failures = [event for event in events if event.get("level") in {"error", "critical"} or "failed" in event.get("kind", "")]
    return {"eventCount": len(events), "failureCount": len(failures), "profiler": profiler_summary()}

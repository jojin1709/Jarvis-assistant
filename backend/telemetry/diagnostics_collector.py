from __future__ import annotations

from environment.runtime_analyzer import runtime_analysis
from events.event_bus import recent_events
from state_machine.workflow_state_manager import current_state
from sync.sync_manager import sync_status


def diagnostics_snapshot() -> dict:
    return {"runtime": runtime_analysis(), "events": recent_events(40), "state": current_state(), "sync": sync_status()}

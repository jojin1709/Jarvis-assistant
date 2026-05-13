from __future__ import annotations

from platform_core.state_store import append_history


def record_event_to_platform(event: dict) -> None:
    append_history({"event": f"event.{event.get('kind')}", "payload": event})


def install_default_handlers() -> None:
    from events.event_bus import subscribe

    subscribe("*", record_event_to_platform)

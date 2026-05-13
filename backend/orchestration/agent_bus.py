from __future__ import annotations

from agents.message_bus import message_bus


def publish_agent_event(sender: str, recipient: str, topic: str, payload: dict) -> dict:
    return message_bus.publish(sender, recipient, topic, payload)


def recent_agent_events(limit: int = 80) -> list[dict]:
    return message_bus.recent(limit=limit)

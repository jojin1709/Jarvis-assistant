from __future__ import annotations

import json
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


BUS_PATH = Path(__file__).resolve().parents[1] / "runtime" / "agent_messages.jsonl"


@dataclass
class AgentMessage:
    sender: str
    recipient: str
    topic: str
    payload: dict
    createdAt: str = ""

    def as_dict(self) -> dict:
        data = asdict(self)
        data["createdAt"] = self.createdAt or datetime.now().isoformat(timespec="seconds")
        return data


class AgentMessageBus:
    def __init__(self) -> None:
        self._queues: dict[str, deque] = defaultdict(deque)

    def publish(self, sender: str, recipient: str, topic: str, payload: dict) -> dict:
        message = AgentMessage(sender, recipient, topic, payload).as_dict()
        self._queues[recipient].append(message)
        BUS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with BUS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(message, ensure_ascii=False) + "\n")
        return message

    def drain(self, recipient: str, limit: int = 40) -> list[dict]:
        messages = []
        queue = self._queues[recipient]
        while queue and len(messages) < limit:
            messages.append(queue.popleft())
        return messages

    def recent(self, limit: int = 80) -> list[dict]:
        if not BUS_PATH.exists():
            return []
        rows = []
        for line in BUS_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return list(reversed(rows))


message_bus = AgentMessageBus()

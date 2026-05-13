from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path


LEARNING_PATH = Path(__file__).resolve().parents[1] / "runtime" / "learning.json"


def record_behavior(kind: str, value: str, outcome: str = "success", metadata: dict | None = None) -> dict:
    data = _load()
    event = {
        "createdAt": datetime.now().isoformat(timespec="seconds"),
        "kind": kind,
        "value": value,
        "outcome": outcome,
        "metadata": metadata or {},
    }
    data.setdefault("events", []).append(event)
    data["events"] = data["events"][-1000:]
    data["preferences"] = _score_preferences(data["events"])
    _save(data)
    return event


def learning_state() -> dict:
    data = _load()
    data["preferences"] = _score_preferences(data.get("events", []))
    return data


def recommend(kind: str, default: str = "") -> str:
    prefs = learning_state().get("preferences", {}).get(kind, [])
    return prefs[0]["value"] if prefs else default


def _score_preferences(events: list[dict]) -> dict:
    grouped: dict[str, Counter] = {}
    for event in events:
        weight = 2 if event.get("outcome") == "success" else -1
        grouped.setdefault(event.get("kind", "unknown"), Counter())[event.get("value", "")] += weight
    return {
        kind: [{"value": value, "score": score} for value, score in counter.most_common(12) if value and score > 0]
        for kind, counter in grouped.items()
    }


def _load() -> dict:
    if not LEARNING_PATH.exists():
        return {"events": [], "preferences": {}}
    try:
        return json.loads(LEARNING_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"events": [], "preferences": {}}


def _save(data: dict) -> None:
    LEARNING_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEARNING_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

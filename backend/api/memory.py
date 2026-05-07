import json
import re
from datetime import datetime
from pathlib import Path


MEMORY_PATH = Path(__file__).resolve().parents[1] / "runtime" / "memory.json"


def _load() -> dict:
    if not MEMORY_PATH.exists():
        return {"facts": []}

    try:
        data = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"facts": []}

    facts = data.get("facts")
    return {"facts": facts if isinstance(facts, list) else []}


def _save(data: dict) -> None:
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def memory_context() -> str:
    facts = _load()["facts"][-12:]
    if not facts:
        return ""
    lines = [str(item.get("text", "")).strip() for item in facts if item.get("text")]
    return "\n".join(f"- {line}" for line in lines)


def handle_memory_command(text: str) -> str | None:
    cleaned = " ".join(text.strip().split())
    normalized = cleaned.lower()

    if normalized in {"what do you remember", "show memory", "show memories", "list memory", "list memories"}:
        context = memory_context()
        return "I do not have saved memories yet." if not context else f"Saved memory:\n{context}"

    if normalized in {"forget everything", "clear memory", "clear memories", "delete memory", "delete memories"}:
        _save({"facts": []})
        return "Memory cleared."

    remember_prefixes = (
        "remember that ",
        "remember ",
        "save memory that ",
        "save memory ",
        "memorize that ",
        "memorize ",
    )
    for prefix in remember_prefixes:
        if normalized.startswith(prefix):
            fact = cleaned[len(prefix) :].strip(" .")
            if not fact:
                return "Tell me what to remember."
            data = _load()
            data["facts"].append({"text": fact, "created_at": datetime.now().isoformat(timespec="seconds")})
            _save(data)
            return f"Remembered: {fact}."

    match = re.search(r"\bmy ([a-zA-Z0-9 _-]{2,40}) is ([^.!?]+)", cleaned, re.IGNORECASE)
    if match and any(word in normalized for word in ("remember", "save", "memorize")):
        fact = f"my {match.group(1).strip()} is {match.group(2).strip()}"
        data = _load()
        data["facts"].append({"text": fact, "created_at": datetime.now().isoformat(timespec="seconds")})
        _save(data)
        return f"Remembered: {fact}."

    return None

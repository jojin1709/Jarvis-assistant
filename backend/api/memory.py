import json
import os
import re
from datetime import datetime
from pathlib import Path


MEMORY_PATH = Path(__file__).resolve().parents[1] / "runtime" / "memory.json"
PLACEHOLDER_NAMES = {"", "operator", "your name", "user"}


def _load() -> dict:
    if not MEMORY_PATH.exists():
        return {"profile": {}, "facts": []}

    try:
        data = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"profile": {}, "facts": []}

    profile = data.get("profile")
    facts = data.get("facts")
    return {
        "profile": profile if isinstance(profile, dict) else {},
        "facts": facts if isinstance(facts, list) else [],
    }


def _save(data: dict) -> None:
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def memory_context() -> str:
    data = _load()
    lines = []
    profile = data["profile"]
    user_name = str(profile.get("user_name") or "").strip()
    interests = profile.get("interests")

    if user_name:
        lines.append(f"Current user's name: {user_name}")
    if isinstance(interests, list) and interests:
        lines.append("Current user's interests: " + ", ".join(str(item) for item in interests[-8:] if item))

    facts = data["facts"][-12:]
    lines.extend(str(item.get("text", "")).strip() for item in facts if item.get("text"))

    if not lines:
        return ""
    return "\n".join(f"- {line}" for line in lines)


def user_display_name(configured_name: str = "") -> str:
    data = _load()
    profile_name = str(data["profile"].get("user_name") or "").strip()
    if profile_name:
        return profile_name

    configured = configured_name.strip()
    if configured and configured.lower() not in PLACEHOLDER_NAMES:
        return configured

    for key in ("USERNAME", "USER"):
        value = os.getenv(key, "").strip()
        if value:
            return value

    return "User"


def profile_summary(configured_name: str = "") -> dict[str, object]:
    data = _load()
    profile = data["profile"]
    return {
        "user_name": user_display_name(configured_name),
        "saved_name": str(profile.get("user_name") or "").strip() or None,
        "interests": profile.get("interests") if isinstance(profile.get("interests"), list) else [],
        "memory_count": len(data["facts"]),
    }


def _save_profile_field(key: str, value: object) -> None:
    data = _load()
    data["profile"][key] = value
    _save(data)


def _append_interest(value: str) -> str:
    interest = value.strip(" .")
    if not interest:
        return "Tell me the interest to remember."

    data = _load()
    interests = data["profile"].get("interests")
    if not isinstance(interests, list):
        interests = []

    if interest.lower() not in {str(item).lower() for item in interests}:
        interests.append(interest)

    data["profile"]["interests"] = interests[-20:]
    _save(data)
    return f"Remembered your interest: {interest}."


def handle_memory_command(text: str) -> str | None:
    cleaned = " ".join(text.strip().split())
    normalized = cleaned.lower()

    name_match = re.match(r"^(?:my name is|call me|set my name to|remember my name is)\s+(.+)$", cleaned, re.IGNORECASE)
    if name_match:
        name = name_match.group(1).strip(" .")
        if not name:
            return "Tell me the name to remember."
        _save_profile_field("user_name", name)
        return f"Got it. I will call you {name}."

    if normalized in {"what is my name", "who am i", "who are you talking to"}:
        return f"Your name is {user_display_name()}."

    if normalized in {"forget my name", "clear my name", "delete my name"}:
        data = _load()
        data["profile"].pop("user_name", None)
        _save(data)
        return "Your saved name was cleared."

    interest_match = re.match(
        r"^(?:my interest is|my interests are|i like|i am interested in|remember my interest is)\s+(.+)$",
        cleaned,
        re.IGNORECASE,
    )
    if interest_match and any(word in normalized for word in ("interest", "like", "remember")):
        return _append_interest(interest_match.group(1))

    if normalized in {"what do you remember", "show memory", "show memories", "list memory", "list memories"}:
        context = memory_context()
        return "I do not have saved memories yet." if not context else f"Saved memory:\n{context}"

    if normalized in {"forget everything", "clear memory", "clear memories", "delete memory", "delete memories"}:
        _save({"profile": {}, "facts": []})
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

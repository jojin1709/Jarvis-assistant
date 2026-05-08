import json
import os
import re
from datetime import datetime
from pathlib import Path

from api.permissions import guard_action, memory_enabled
from providers.secure_store import save_secret


MEMORY_PATH = Path(__file__).resolve().parents[1] / "runtime" / "memory.json"
PROVIDER_KEYS_PATH = Path(__file__).resolve().parents[1] / "runtime" / "provider_keys.json"
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
    if not memory_enabled():
        return ""
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
        "onboarding_complete": bool(profile.get("onboarding_complete")),
        "user_type": profile.get("user_type") or "General Use",
        "theme": profile.get("theme") or "dark",
        "ai_provider": profile.get("ai_provider") or "groq",
        "personality": profile.get("personality") or "professional",
        "workspace_paths": profile.get("workspace_paths") if isinstance(profile.get("workspace_paths"), list) else [],
        "memory_storage_path": profile.get("memory_storage_path") or "",
        "voice_activation": bool(profile.get("voice_activation", True)),
        "manual_activation_only": bool(profile.get("manual_activation_only", False)),
        "interests": profile.get("interests") if isinstance(profile.get("interests"), list) else [],
        "memory_count": len(data["facts"]),
        "memory_enabled": memory_enabled(),
    }


def _save_profile_field(key: str, value: object) -> None:
    data = _load()
    data["profile"][key] = value
    _save(data)


def save_profile(patch: dict) -> dict:
    data = _load()
    profile = data["profile"]
    allowed = {
        "user_name",
        "user_type",
        "theme",
        "ai_provider",
        "workspace_paths",
        "memory_storage_path",
        "voice_activation",
        "manual_activation_only",
        "onboarding_complete",
        "onboarding_completed_at",
        "preferences",
        "personality",
    }
    for key, value in patch.items():
        if key in allowed:
            profile[key] = value
    _save(data)
    return profile_summary()


def save_provider_key(provider: str, api_key: str) -> None:
    provider = provider.strip().lower()
    api_key = api_key.strip()
    if not provider or not api_key:
        return

    save_secret(provider, api_key)


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

    if normalized in {"what do you remember", "show memory", "show memories", "list memory", "list memories"}:
        if not memory_enabled():
            return "Memory is disabled in Security & Permissions."
        context = memory_context()
        return "I do not have saved memories yet." if not context else f"Saved memory:\n{context}"

    if normalized in {"forget everything", "clear memory", "clear memories", "delete memory", "delete memories"}:
        return clear_memory()

    if not memory_enabled() and any(word in normalized for word in ("remember", "memorize", "save memory", "my name is", "call me")):
        return "Memory is disabled in Security & Permissions."

    name_match = re.match(r"^(?:my name is|call me|set my name to|remember my name is)\s+(.+)$", cleaned, re.IGNORECASE)
    if name_match:
        name = name_match.group(1).strip(" .")
        if not name:
            return "Tell me the name to remember."
        return guard_action("memory.write", f"remember name {name}", lambda: (_save_profile_field("user_name", name) or f"Got it. I will call you {name}."))

    if normalized in {"what is my name", "who am i", "who are you talking to"}:
        return f"Your name is {user_display_name()}."

    if normalized in {"forget my name", "clear my name", "delete my name"}:
        data = _load()
        data["profile"].pop("user_name", None)
        return guard_action("memory.write", "clear saved name", lambda: (_save(data) or "Your saved name was cleared."))

    interest_match = re.match(
        r"^(?:my interest is|my interests are|i like|i am interested in|remember my interest is)\s+(.+)$",
        cleaned,
        re.IGNORECASE,
    )
    if interest_match and any(word in normalized for word in ("interest", "like", "remember")):
        interest_value = interest_match.group(1)
        return guard_action("memory.write", f"remember interest {interest_value}", lambda: _append_interest(interest_value))

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
            def run() -> str:
                data["facts"].append({"text": fact, "created_at": datetime.now().isoformat(timespec="seconds")})
                _save(data)
                return f"Remembered: {fact}."

            return guard_action("memory.write", f"remember {fact}", run)

    match = re.search(r"\bmy ([a-zA-Z0-9 _-]{2,40}) is ([^.!?]+)", cleaned, re.IGNORECASE)
    if match and any(word in normalized for word in ("remember", "save", "memorize")):
        fact = f"my {match.group(1).strip()} is {match.group(2).strip()}"
        data = _load()
        def run() -> str:
            data["facts"].append({"text": fact, "created_at": datetime.now().isoformat(timespec="seconds")})
            _save(data)
            return f"Remembered: {fact}."

        return guard_action("memory.write", f"remember {fact}", run)

    return None


def clear_memory() -> str:
    return guard_action("memory.clear", "clear Jarvis memory", _clear_memory)


def _clear_memory() -> str:
    _save({"profile": {}, "facts": []})
    return "Memory cleared."


def export_memory() -> dict:
    return _load()

import json
import re
import time
from pathlib import Path
from typing import Mapping


RUNTIME_DIR = Path(__file__).resolve().parents[1] / "runtime"
LIMITS_PATH = RUNTIME_DIR / "groq_rate_limits.json"
RATE_HEADERS = (
    "retry-after",
    "x-ratelimit-limit-requests",
    "x-ratelimit-limit-tokens",
    "x-ratelimit-remaining-requests",
    "x-ratelimit-remaining-tokens",
    "x-ratelimit-reset-requests",
    "x-ratelimit-reset-tokens",
)


def groq_model_available(model: str) -> tuple[bool, str]:
    entry = _load().get(model, {})
    cooldown_until = float(entry.get("cooldown_until") or 0)
    if cooldown_until <= time.time():
        return True, ""
    return False, f"{model} cooling down for {_format_wait(cooldown_until - time.time())}"


def groq_limit_snapshot() -> dict:
    now = time.time()
    snapshot = {}
    for model, entry in _load().items():
        if not isinstance(entry, dict):
            continue
        cooldown_until = float(entry.get("cooldown_until") or 0)
        remaining = max(0, int(cooldown_until - now)) if cooldown_until > now else 0
        snapshot[model] = {
            "cooldownRemainingSeconds": remaining,
            "cooldownReason": entry.get("cooldown_reason", ""),
            "headers": entry.get("headers", {}),
            "updatedAt": entry.get("updated_at"),
        }
    return snapshot


def remember_groq_headers(model: str, headers: Mapping[str, str] | None) -> None:
    normalized = _normalize_headers(headers)
    if not normalized:
        return

    data = _load()
    entry = data.get(model, {})
    entry["headers"] = normalized
    entry["updated_at"] = time.time()

    token_remaining = _to_int(normalized.get("x-ratelimit-remaining-tokens"))
    request_remaining = _to_int(normalized.get("x-ratelimit-remaining-requests"))
    cooldown_seconds = 0.0
    if token_remaining == 0:
        cooldown_seconds = max(cooldown_seconds, _duration_seconds(normalized.get("x-ratelimit-reset-tokens")))
    if request_remaining == 0:
        cooldown_seconds = max(cooldown_seconds, _duration_seconds(normalized.get("x-ratelimit-reset-requests")))
    if cooldown_seconds > 0:
        entry["cooldown_until"] = time.time() + cooldown_seconds
        entry["cooldown_reason"] = "Groq response headers showed no remaining request or token quota."
    elif float(entry.get("cooldown_until") or 0) <= time.time():
        entry.pop("cooldown_until", None)
        entry.pop("cooldown_reason", None)

    data[model] = entry
    _save(data)


def remember_groq_rate_limit(model: str, headers: Mapping[str, str] | None, error_text: str = "") -> None:
    normalized = _normalize_headers(headers)
    retry_after = _duration_seconds(normalized.get("retry-after"))
    reset_tokens = _duration_seconds(normalized.get("x-ratelimit-reset-tokens"))
    reset_requests = _duration_seconds(normalized.get("x-ratelimit-reset-requests"))
    text_wait = _duration_seconds(_extract_try_again(error_text))
    cooldown_seconds = max(retry_after, reset_tokens, reset_requests, text_wait, 15.0)

    data = _load()
    entry = data.get(model, {})
    entry["headers"] = normalized
    entry["updated_at"] = time.time()
    entry["cooldown_until"] = time.time() + cooldown_seconds
    entry["cooldown_reason"] = "Groq returned 429 rate limit."
    data[model] = entry
    _save(data)


def _normalize_headers(headers: Mapping[str, str] | None) -> dict[str, str]:
    if not headers:
        return {}
    normalized = {}
    for key in RATE_HEADERS:
        value = headers.get(key) if hasattr(headers, "get") else None
        if value is not None:
            normalized[key] = str(value)
    return normalized


def _duration_seconds(value: str | None) -> float:
    if not value:
        return 0.0
    text = str(value).strip().lower()
    try:
        return max(0.0, float(text))
    except ValueError:
        pass

    total = 0.0
    for amount, unit in re.findall(r"(\d+(?:\.\d+)?)(ms|h|m|s)", text):
        number = float(amount)
        if unit == "ms":
            total += number / 1000
        elif unit == "h":
            total += number * 3600
        elif unit == "m":
            total += number * 60
        elif unit == "s":
            total += number
    return total


def _extract_try_again(text: str) -> str:
    match = re.search(r"try again in\s+([^.'\"}]+)", text or "", flags=re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _format_wait(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _to_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(float(str(value).strip()))
    except ValueError:
        return None


def _load() -> dict:
    if not LIMITS_PATH.exists():
        return {}
    try:
        data = json.loads(LIMITS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _save(data: dict) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    LIMITS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

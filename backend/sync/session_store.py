from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.config import BACKEND_DIR
from providers.secure_store import get_secret, has_secret, save_secret


CONFIG_PATH = BACKEND_DIR / "runtime" / "sync" / "providers.json"


def provider_config(provider: str) -> dict:
    data = _load()
    return data.get(provider, {})


def save_provider_config(provider: str, config: dict) -> dict:
    data = _load()
    safe = {key: value for key, value in config.items() if key != "clientSecret"}
    data[provider] = {**data.get(provider, {}), **safe, "updatedAt": _now()}
    if config.get("clientSecret"):
        save_secret(f"sync_{provider}_client_secret", str(config["clientSecret"]))
    _save(data)
    return provider_state(provider)


def save_provider_token(provider: str, token: dict) -> None:
    if token.get("refreshToken"):
        save_secret(f"sync_{provider}_refresh_token", str(token["refreshToken"]))
    if token.get("accessToken"):
        save_secret(f"sync_{provider}_access_token", str(token["accessToken"]))
    data = _load()
    data[provider] = {**data.get(provider, {}), "expiresAt": token.get("expiresAt", ""), "connectedAt": _now(), "updatedAt": _now()}
    _save(data)


def provider_state(provider: str) -> dict:
    config = provider_config(provider)
    return {
        "provider": provider,
        "configured": bool(config.get("clientId")),
        "connected": has_secret(f"sync_{provider}_refresh_token"),
        "redirectUri": config.get("redirectUri", ""),
        "expiresAt": config.get("expiresAt", ""),
        "updatedAt": config.get("updatedAt", ""),
    }


def access_token(provider: str) -> str:
    return get_secret(f"sync_{provider}_access_token")


def _load() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _save(data: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")

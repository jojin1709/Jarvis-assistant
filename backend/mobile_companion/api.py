from __future__ import annotations

import json
import os
import secrets
import socket
from datetime import datetime
from pathlib import Path


NOTIFICATIONS_PATH = Path(__file__).resolve().parents[1] / "runtime" / "mobile_notifications.json"
_pairing_token = ""


def push_mobile_notification(title: str, body: str, level: str = "info", action: dict | None = None) -> dict:
    data = _load()
    item = {
        "id": f"mobile-{len(data) + 1}",
        "createdAt": datetime.now().isoformat(timespec="seconds"),
        "title": title,
        "body": body,
        "level": level,
        "action": action or {},
        "read": False,
    }
    data.append(item)
    _save(data[-200:])
    return item


def mobile_state() -> dict:
    enabled = os.getenv("JX_JARVIS_MOBILE_ENABLED", "false").strip().lower() == "true"
    notifications = list(reversed(_load()[-80:]))
    if not enabled:
        return {
            "enabled": False,
            "reason": "Set JX_JARVIS_MOBILE_ENABLED=true in .env to activate mobile companion.",
            "notifications": notifications,
            "capabilities": ["monitor", "approve", "notify"],
        }

    host = _local_ip()
    port = int(os.getenv("JX_JARVIS_BACKEND_PORT", "8765"))
    token = _get_or_create_token()
    return {
        "enabled": True,
        "host": host,
        "port": port,
        "endpoint": f"http://{host}:{port}",
        "pairingToken": token,
        "qrData": f"jxjarvis://{host}:{port}?token={token}",
        "notifications": notifications,
        "capabilities": ["monitor", "approve", "notify"],
    }


def _local_ip() -> str:
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        if sock:
            sock.close()


def _get_or_create_token() -> str:
    global _pairing_token
    if not _pairing_token:
        _pairing_token = secrets.token_urlsafe(16)
    return _pairing_token


def _load() -> list[dict]:
    if not NOTIFICATIONS_PATH.exists():
        return []
    try:
        data = json.loads(NOTIFICATIONS_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(data: list[dict]) -> None:
    NOTIFICATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTIFICATIONS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

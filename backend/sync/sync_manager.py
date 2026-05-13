from __future__ import annotations

from datetime import datetime
from pathlib import Path

from events.event_bus import emit_event
from sync import dropbox, google_drive, onedrive
from sync.backup_manager import create_encrypted_backup, inspect_backup, restore_backup
from sync.encryption import encryption_status
from sync.sync_scheduler import sync_schedule


PROVIDERS = {"google_drive": google_drive, "dropbox": dropbox, "onedrive": onedrive}


def sync_status() -> dict:
    return {
        "enabled": False,
        "mode": "local-first",
        "providers": {name: module.status() for name, module in PROVIDERS.items()},
        "encryption": encryption_status(),
        "schedule": sync_schedule(),
        "protectedData": ["browser profiles", "raw cookies", "provider key store", ".env files", "virtual environments"],
    }


def configure_provider(provider: str, payload: dict) -> dict:
    module = _provider(provider)
    return module.configure(str(payload.get("clientId") or ""), str(payload.get("clientSecret") or ""), str(payload.get("redirectUri") or "http://127.0.0.1:8765/api/sync/oauth/callback"))


def provider_auth_url(provider: str, redirect_uri: str = "", client_id: str = "") -> dict:
    module = _provider(provider)
    return module.auth_url(redirect_uri or "http://127.0.0.1:8765/api/sync/oauth/callback", client_id or None)


def connect_provider(provider: str, payload: dict) -> dict:
    module = _provider(provider)
    result = module.save_token(str(payload.get("refreshToken") or ""), str(payload.get("accessToken") or ""), str(payload.get("expiresAt") or ""))
    emit_event("sync.provider_connected", {"provider": provider})
    return result


def run_backup_sync(provider: str | None = None, scope: list[str] | None = None) -> dict:
    backup = create_encrypted_backup(scope)
    target = provider or "local"
    result = {"ok": True, "provider": target, "uploaded": False, "backup": backup, "completedAt": datetime.now().isoformat(timespec="seconds")}
    if provider:
        module = _provider(provider)
        upload = module.upload_file(backup["path"], f"backups/{Path(backup['path']).name}")
        result["uploaded"] = bool(upload.get("ok"))
        result["upload"] = upload
    emit_event("sync.backup_created", {"provider": target, "path": backup["path"], "bytes": backup["bytes"]})
    return result


def restore_sync_backup(path: str, target: str | None = None) -> dict:
    result = restore_backup(path, target)
    emit_event("sync.backup_restored", {"path": path, "restoredTo": result["restoredTo"]})
    return result


def inspect_sync_backup(path: str) -> dict:
    return inspect_backup(path)


def _provider(provider: str):
    key = provider.strip().lower()
    if key not in PROVIDERS:
        raise ValueError(f"Unsupported sync provider: {provider}")
    return PROVIDERS[key]

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime
from pathlib import Path

from app.config import BACKEND_DIR, PROJECT_DIR
from sync.encryption import decrypt_bytes, encrypt_bytes


RUNTIME_SYNC_DIR = BACKEND_DIR / "runtime" / "sync"
RESTORE_DIR = BACKEND_DIR / "runtime" / "restored_sync"

SAFE_ROOTS = {
    "workflows": BACKEND_DIR / "runtime" / "workflows",
    "memory": BACKEND_DIR / "runtime",
    "skills": BACKEND_DIR / "skills",
    "plugins": BACKEND_DIR / "plugins",
    "configs": PROJECT_DIR,
}

DENY_PARTS = {
    ".env",
    ".venv",
    "profiles",
    "provider_keys.secure.json",
    "node_modules",
    "dist",
    "__pycache__",
    ".git",
}


def create_encrypted_backup(scope: list[str] | None = None) -> dict:
    selected = _selected_scope(scope)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    bundle_path = RUNTIME_SYNC_DIR / f"jarvis-backup-{timestamp}.jvbackup"
    manifest = {"createdAt": datetime.now().isoformat(timespec="seconds"), "scope": selected, "files": []}
    plain = io.BytesIO()
    with zipfile.ZipFile(plain, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for label in selected:
            root = SAFE_ROOTS[label]
            if not root.exists():
                continue
            for path in _safe_files(root):
                arcname = f"{label}/{path.relative_to(root).as_posix()}"
                archive.write(path, arcname)
                manifest["files"].append({"path": arcname, "bytes": path.stat().st_size})
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
    RUNTIME_SYNC_DIR.mkdir(parents=True, exist_ok=True)
    bundle_path.write_bytes(encrypt_bytes(plain.getvalue()))
    return {"ok": True, "path": str(bundle_path), "manifest": manifest, "bytes": bundle_path.stat().st_size}


def inspect_backup(path: str) -> dict:
    bundle = Path(path)
    with zipfile.ZipFile(io.BytesIO(decrypt_bytes(bundle.read_bytes()))) as archive:
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
    return {"ok": True, "path": str(bundle), "manifest": manifest}


def restore_backup(path: str, target: str | None = None) -> dict:
    target_dir = Path(target) if target else RESTORE_DIR / datetime.now().strftime("%Y%m%d-%H%M%S")
    target_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(decrypt_bytes(Path(path).read_bytes()))) as archive:
        for member in archive.infolist():
            if member.filename == "manifest.json" or member.is_dir():
                continue
            destination = (target_dir / member.filename).resolve()
            if not str(destination).startswith(str(target_dir.resolve())):
                raise ValueError("Unsafe path in backup archive.")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(member.filename))
    return {"ok": True, "restoredTo": str(target_dir)}


def _selected_scope(scope: list[str] | None) -> list[str]:
    if not scope:
        return ["workflows", "memory", "skills", "plugins", "configs"]
    return [item for item in scope if item in SAFE_ROOTS]


def _safe_files(root: Path):
    if root.is_file():
        yield root
        return
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        parts = set(path.relative_to(root).parts)
        if parts & DENY_PARTS:
            continue
        if path.suffix.lower() in {".sqlite", ".db-wal", ".db-shm"} and "provider" in path.name.lower():
            continue
        yield path

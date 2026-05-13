from __future__ import annotations

from pathlib import Path

from release_security.signature_verifier import sha256_file


def validate_release_artifact(path: str) -> dict:
    artifact = Path(path)
    checks = {
        "exists": artifact.exists(),
        "isFile": artifact.is_file(),
        "extensionOk": artifact.suffix.lower() in {".exe", ".msi", ".zip", ".blockmap", ".yml"},
    }
    ok = all(checks.values())
    return {"ok": ok, "path": str(artifact), "checks": checks, "sha256": sha256_file(str(artifact)) if artifact.exists() and artifact.is_file() else ""}

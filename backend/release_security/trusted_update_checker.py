from __future__ import annotations

from release_security.signature_verifier import verify_sha256


def validate_update_manifest(manifest: dict) -> dict:
    required = {"version", "url", "sha256"}
    missing = sorted(required - set(manifest))
    return {"ok": not missing, "missing": missing, "manifest": {key: manifest.get(key) for key in sorted(required)}}


def verify_downloaded_update(path: str, manifest: dict) -> dict:
    manifest_check = validate_update_manifest(manifest)
    if not manifest_check["ok"]:
        return manifest_check
    return verify_sha256(path, str(manifest["sha256"]))

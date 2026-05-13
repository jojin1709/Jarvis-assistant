from __future__ import annotations

import os


def signing_config() -> dict:
    return {
        "enabled": bool(os.getenv("JX_JARVIS_SIGNING_CERT_PATH")),
        "certificatePath": os.getenv("JX_JARVIS_SIGNING_CERT_PATH", ""),
        "timestampServer": os.getenv("JX_JARVIS_TIMESTAMP_SERVER", "http://timestamp.digicert.com"),
        "tool": "signtool.exe",
    }


def signing_command(artifact_path: str) -> dict:
    config = signing_config()
    if not config["enabled"]:
        return {"ok": False, "message": "Code signing certificate is not configured.", "config": config}
    command = [
        "signtool",
        "sign",
        "/fd",
        "SHA256",
        "/tr",
        config["timestampServer"],
        "/td",
        "SHA256",
        "/f",
        config["certificatePath"],
        artifact_path,
    ]
    return {"ok": True, "command": command, "config": config}

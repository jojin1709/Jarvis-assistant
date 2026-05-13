from __future__ import annotations

import shutil
import subprocess


def docker_status() -> dict:
    if not shutil.which("docker"):
        return {"available": False, "message": "Docker is not installed or not on PATH."}
    try:
        result = subprocess.run(["docker", "ps", "--format", "{{json .}}"], capture_output=True, text=True, timeout=8, check=False)
        containers = []
        import json

        for line in result.stdout.splitlines():
            try:
                containers.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return {"available": True, "ok": result.returncode == 0, "containers": containers, "stderr": result.stderr}
    except Exception as error:
        return {"available": True, "ok": False, "error": str(error)}


def environment_report() -> dict:
    import os
    import platform

    return {
        "os": platform.platform(),
        "node": _version(["node", "--version"]),
        "npm": _version(["npm", "--version"]),
        "python": _version(["python", "--version"]),
        "git": _version(["git", "--version"]),
        "docker": docker_status(),
        "pathEntries": len(os.getenv("PATH", "").split(";")),
    }


def _version(command: list[str]) -> str:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5, check=False)
        return (result.stdout or result.stderr).strip()
    except Exception:
        return ""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from api.permissions import evaluate_permission, log_activity


DEFAULT_IMAGE = "python:3.11-slim"


def docker_available() -> bool:
    return bool(shutil.which("docker"))


def run_in_docker(command: str, workspace: str | Path, image: str = DEFAULT_IMAGE, timeout: int = 180) -> dict:
    root = Path(workspace).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        return {"ok": False, "error": f"Workspace does not exist: {root}"}
    if not docker_available():
        return {"ok": False, "error": "Docker is not available on PATH.", "sandbox": "docker"}
    decision = evaluate_permission("terminal.run", f"docker sandbox command: {command}", path=root, command=command)
    if not decision.allowed or decision.requires_confirmation:
        return {"ok": False, "error": decision.message, "sandbox": "docker"}
    docker_command = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--cpus",
        "1",
        "--memory",
        "1g",
        "-v",
        f"{root}:/workspace:rw",
        "-w",
        "/workspace",
        image,
        "sh",
        "-lc",
        command,
    ]
    try:
        result = subprocess.run(docker_command, capture_output=True, text=True, timeout=timeout, check=False)
        ok = result.returncode == 0
        log_activity(f"Docker sandbox command {'completed' if ok else 'failed'}: {command}", "success" if ok else "error", "sandbox")
        return {
            "ok": ok,
            "sandbox": "docker",
            "image": image,
            "returnCode": result.returncode,
            "stdout": result.stdout[-8000:],
            "stderr": result.stderr[-8000:],
        }
    except subprocess.TimeoutExpired as error:
        return {"ok": False, "sandbox": "docker", "error": f"Sandbox timed out after {timeout}s.", "stdout": error.stdout or "", "stderr": error.stderr or ""}

from __future__ import annotations

from pathlib import Path


def detect_dependency_managers(path: str | Path) -> dict:
    root = Path(path).expanduser().resolve()
    return {
        "npm": (root / "package.json").exists(),
        "python": (root / "requirements.txt").exists() or (root / "pyproject.toml").exists(),
        "docker": (root / "Dockerfile").exists() or (root / "docker-compose.yml").exists(),
    }


def install_plan(path: str | Path) -> list[str]:
    managers = detect_dependency_managers(path)
    commands = []
    if managers["npm"]:
        commands.append("npm install")
    if managers["python"]:
        commands.append("python -m pip install -r requirements.txt")
    if managers["docker"]:
        commands.append("docker compose build")
    return commands

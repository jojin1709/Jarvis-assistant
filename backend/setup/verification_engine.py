from __future__ import annotations

from setup.dependency_manager import detect_dependency_managers


def verification_commands(path: str) -> list[str]:
    managers = detect_dependency_managers(path)
    commands = []
    if managers["npm"]:
        commands.append("npm run build")
    if managers["python"]:
        commands.append("python -m compileall .")
    if managers["docker"]:
        commands.append("docker compose config")
    return commands

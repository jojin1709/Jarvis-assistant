from __future__ import annotations

from setup.dependency_manager import install_plan


def prepare_environment(path: str, execute: bool = False) -> dict:
    commands = install_plan(path)
    if not execute:
        return {"ok": True, "path": path, "commands": commands, "executed": False}
    from terminal.service import terminal_service

    results = [terminal_service.run_sync(command, cwd=path, timeout=600).as_dict() for command in commands]
    return {"ok": all(item.get("status") == "completed" for item in results), "path": path, "commands": commands, "results": results, "executed": True}

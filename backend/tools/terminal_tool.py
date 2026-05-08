import subprocess

from api.permissions import guard_action
from safety.policy import command_risk


SAFE_TERMINAL_COMMANDS = {
    "node --version",
    "npm --version",
    "python --version",
    "py --version",
    "git status",
}


def run_terminal_tool(text: str) -> str | None:
    normalized = " ".join(text.strip().split())
    lowered = normalized.lower()
    prefixes = ("run terminal command ", "execute terminal command ", "terminal ")
    for prefix in prefixes:
        if lowered.startswith(prefix):
            command = normalized[len(prefix) :].strip()
            return run_terminal_command(command)

    if lowered in SAFE_TERMINAL_COMMANDS:
        return run_terminal_command(normalized)

    return None


def run_terminal_command(command: str, cwd: str | None = None) -> str:
    normalized = " ".join(command.strip().split())
    risk = command_risk(normalized)
    if not risk["allowed"]:
        return str(risk["reason"])

    if normalized not in SAFE_TERMINAL_COMMANDS:
        return "Terminal command blocked. Only safe diagnostic commands are allowed from autonomous workflows."

    def run() -> str:
        result = subprocess.run(
            normalized.split(),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        output = (result.stdout or result.stderr or "").strip()
        return output or f"Command exited with code {result.returncode}."

    return guard_action("terminal.run", f"run terminal command {normalized}", run, command=normalized)

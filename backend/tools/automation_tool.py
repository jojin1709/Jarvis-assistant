from tools.terminal_tool import run_terminal_command


SAFE_AUTOMATIONS = {
    "check developer tools": [
        "node --version",
        "npm --version",
        "python --version",
        "git status",
    ],
    "check project status": [
        "git status",
    ],
}


def run_automation_command(text: str) -> str | None:
    normalized = " ".join(text.lower().strip().split())

    for name, commands in SAFE_AUTOMATIONS.items():
        if name in normalized:
            results = [f"{command}: {run_terminal_command(command)}" for command in commands]
            return "\n".join(results)

    if "run diagnostic" in normalized or "check system tools" in normalized:
        results = [f"{command}: {run_terminal_command(command)}" for command in SAFE_AUTOMATIONS["check developer tools"]]
        return "\n".join(results)

    return None

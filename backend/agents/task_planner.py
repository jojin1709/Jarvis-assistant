from dataclasses import dataclass


@dataclass
class PlanStep:
    label: str
    tool_hint: str = "auto"
    risk: str = "low"


def build_execution_plan(text: str) -> list[PlanStep]:
    command = " ".join(text.strip().split())
    if not command:
        return []

    parts = _split_steps(command)
    return [PlanStep(label=part, tool_hint=_tool_hint(part), risk=_risk(part)) for part in parts[:8]]


def _split_steps(text: str) -> list[str]:
    lowered = text
    for separator in (" and then ", " then ", ";"):
        lowered = lowered.replace(separator, "|")
    parts = [part.strip(" .") for part in lowered.split("|") if part.strip(" .")]
    return parts or [text]


def _tool_hint(step: str) -> str:
    normalized = step.lower()
    if any(word in normalized for word in ("remember", "memory", "my name")):
        return "memory"
    if any(word in normalized for word in ("website", "portfolio", "app", "code", "project")) and any(
        word in normalized for word in ("create", "build", "make", "generate", "write")
    ):
        return "code"
    if any(word in normalized for word in ("google", "youtube", "browser", "website", "click", "scroll", "summarize page")):
        return "browser"
    if any(word in normalized for word in ("file", "folder", "desktop", "documents", "downloads", "rename", "delete", "move")):
        return "file"
    if any(word in normalized for word in ("terminal", "command", "npm", "python", "git")):
        return "terminal"
    if any(word in normalized for word in ("open", "launch", "close", "quit")):
        return "app"
    return "auto"


def _risk(step: str) -> str:
    normalized = step.lower()
    if any(word in normalized for word in ("delete", "remove", "shutdown", "restart", "terminal", "payment", "password", "login")):
        return "high"
    if any(word in normalized for word in ("create", "edit", "move", "rename", "browser", "click", "download")):
        return "medium"
    return "low"

import re


DANGEROUS_COMMAND_PATTERNS = (
    r"\brm\s+-rf\b",
    r"\bdel\s+/[fsq]\b",
    r"\brmdir\s+/s\b",
    r"\bformat\s+[a-z]:",
    r"\bdiskpart\b",
    r"\breg\s+delete\b",
    r"\bshutdown\b",
    r"\brestart-computer\b",
    r"\bstop-computer\b",
    r"\bset-executionpolicy\b",
    r"\bInvoke-Expression\b",
    r"\biex\b",
    r"\bcurl\b.+\|\s*(bash|sh|powershell)",
)


def command_risk(command: str) -> dict[str, object]:
    normalized = " ".join(command.strip().split())
    lowered = normalized.lower()
    for pattern in DANGEROUS_COMMAND_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            return {
                "allowed": False,
                "risk": "high",
                "reason": "Dangerous command pattern blocked by Jarvis safety policy.",
                "pattern": pattern,
            }
    return {"allowed": True, "risk": "low", "reason": "No dangerous command pattern detected.", "pattern": ""}

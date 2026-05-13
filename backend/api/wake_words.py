WAKE_PHRASES = (
    "hey jarvis",
    "hi jarvis",
    "hello jarvis",
    "ok jarvis",
    "okay jarvis",
    "jarvis",
    "ഹേ ജാർവിസ്",
    "ഹായ് ജാർവിസ്",
    "ജാർവിസ്",
    "ജാര്‍വിസ്",
)


def wake_command_from(text: str) -> tuple[bool, str]:
    normalized = " ".join(text.lower().strip().split())
    for phrase in WAKE_PHRASES:
        if phrase in normalized:
            command = normalized.split(phrase, 1)[1].strip(" ,:.-")
            return True, command
    return False, ""

from __future__ import annotations

from api.wake_words import wake_command_from
from voice.microphone_manager import update_voice_preferences, voice_preferences


def wake_state() -> dict:
    prefs = voice_preferences()
    return {"enabled": bool(prefs.get("wakeEnabled")), "mode": prefs.get("mode", "push_to_talk"), "backgroundVoice": bool(prefs.get("backgroundVoice"))}


def set_voice_mode(mode: str) -> dict:
    normalized = mode if mode in {"push_to_talk", "continuous", "silent", "background"} else "push_to_talk"
    patch = {"mode": normalized, "silentMode": normalized == "silent", "backgroundVoice": normalized in {"continuous", "background", "push_to_talk"}}
    return update_voice_preferences(patch)


def parse_wake_phrase(text: str) -> dict:
    awakened, command = wake_command_from(text)
    return {"awakened": awakened, "command": command, "transcript": text}

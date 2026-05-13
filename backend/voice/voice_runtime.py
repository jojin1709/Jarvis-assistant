from __future__ import annotations

import json
import threading
from datetime import datetime

from app.config import BACKEND_DIR
from events.event_bus import emit_event
from voice.microphone_manager import list_microphones, update_voice_preferences, voice_preferences


STATE_PATH = BACKEND_DIR / "runtime" / "voice" / "runtime_state.json"


class VoiceRuntime:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._state = self._load()

    def start(self) -> dict:
        with self._lock:
            self._state.update({"enabled": True, "status": "idle", "startedAt": _now(), "updatedAt": _now()})
            self._save()
        emit_event("voice.runtime_started", {"mode": self._state.get("mode")})
        return self.status()

    def stop(self) -> dict:
        with self._lock:
            self._state.update({"enabled": False, "status": "disabled", "updatedAt": _now()})
            self._save()
        emit_event("voice.runtime_stopped", {})
        return self.status()

    def set_mode(self, mode: str) -> dict:
        preferences = update_voice_preferences({"mode": mode, "silentMode": mode == "silent"})
        with self._lock:
            self._state.update({"mode": preferences["mode"], "muted": bool(preferences.get("silentMode")), "updatedAt": _now()})
            self._save()
        emit_event("voice.mode_changed", {"mode": preferences["mode"]})
        return self.status()

    def mute(self, muted: bool = True) -> dict:
        update_voice_preferences({"silentMode": muted})
        with self._lock:
            self._state.update({"muted": muted, "updatedAt": _now()})
            self._save()
        emit_event("voice.mute_changed", {"muted": muted})
        return self.status()

    def mark(self, status: str, detail: str = "", transcript: str = "", response: str = "") -> dict:
        with self._lock:
            self._state.update({"status": status, "detail": detail, "updatedAt": _now()})
            if transcript:
                self._state["lastTranscript"] = transcript
            if response:
                self._state["lastResponse"] = response
            self._save()
        emit_event(f"voice.{status}", {"detail": detail, "transcript": transcript})
        return self.status()

    def status(self) -> dict:
        with self._lock:
            preferences = voice_preferences()
            return {
                **self._state,
                "preferences": preferences,
                "microphones": list_microphones(),
                "hotkey": "Space+M",
                "modes": ["push_to_talk", "continuous", "silent", "background"],
            }

    def _load(self) -> dict:
        fallback = {"enabled": True, "status": "idle", "mode": voice_preferences().get("mode", "push_to_talk"), "muted": bool(voice_preferences().get("silentMode")), "updatedAt": _now()}
        if not STATE_PATH.exists():
            return fallback
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            return {**fallback, **(data if isinstance(data, dict) else {})}
        except json.JSONDecodeError:
            return fallback

    def _save(self) -> None:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(self._state, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


voice_runtime = VoiceRuntime()

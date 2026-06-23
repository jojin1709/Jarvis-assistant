from __future__ import annotations

import json
from datetime import datetime

try:
    import sounddevice as sd
except Exception:  # pragma: no cover - depends on host audio drivers and optional package install
    sd = None

try:
    import speech_recognition as sr
except Exception:  # pragma: no cover - optional voice dependency
    sr = None

from app.config import BACKEND_DIR


PREFERENCES_PATH = BACKEND_DIR / "runtime" / "voice" / "preferences.json"


DEFAULT_PREFERENCES = {
    "preferredMicrophone": None,
    "preferredVoice": "",
    "mode": "push_to_talk",
    "wakeEnabled": True,
    "backgroundVoice": True,
    "silentMode": False,
    "language": "auto",
    "listenDurationSeconds": 6,
}


def list_microphones() -> list[dict]:
    if sd is None:
        return []
    try:
        devices = sd.query_devices()
    except Exception:
        return []
    result = []
    for index, device in enumerate(devices):
        if int(device.get("max_input_channels") or 0) <= 0:
            continue
        result.append(
            {
                "index": index,
                "name": str(device.get("name") or f"Microphone {index}"),
                "hostApi": int(device.get("hostapi") or 0),
                "channels": int(device.get("max_input_channels") or 0),
                "defaultSampleRate": int(float(device.get("default_samplerate") or 16000)),
            }
        )
    return result


def voice_preferences() -> dict:
    if not PREFERENCES_PATH.exists():
        return {**DEFAULT_PREFERENCES}
    try:
        data = json.loads(PREFERENCES_PATH.read_text(encoding="utf-8"))
        return {**DEFAULT_PREFERENCES, **(data if isinstance(data, dict) else {})}
    except json.JSONDecodeError:
        return {**DEFAULT_PREFERENCES}


def update_voice_preferences(patch: dict) -> dict:
    preferences = voice_preferences()
    for key in DEFAULT_PREFERENCES:
        if key in patch:
            preferences[key] = patch[key]
    preferences["updatedAt"] = datetime.now().isoformat(timespec="seconds")
    PREFERENCES_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREFERENCES_PATH.write_text(json.dumps(preferences, indent=2), encoding="utf-8")
    return preferences


def listen_with_vad(recognizer, source, timeout: int = 5, phrase_limit: int = 15):
    if sr is None:
        return None
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = 300
    try:
        return recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
    except sr.WaitTimeoutError:
        return None

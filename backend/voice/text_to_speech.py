from __future__ import annotations

import os
import subprocess
from pathlib import Path

from app.config import settings
from voice.speaker import EdgeSpeaker


class TextToSpeechEngine:
    def __init__(self) -> None:
        self.edge = EdgeSpeaker()

    def speak(self, text: str, language: str = "en", interrupt: bool = True, silent: bool = False) -> dict:
        if silent:
            return {"ok": True, "spoken": False, "audioFile": None, "engine": "silent"}
        piper = _piper_command(text)
        if piper:
            return piper
        audio_path = self.edge.speak(text, language=language)
        return {"ok": True, "spoken": True, "audioFile": str(audio_path), "engine": settings.tts_provider or "edge"}


def _piper_command(text: str) -> dict | None:
    binary = os.getenv("PIPER_BINARY", "").strip()
    voice = os.getenv("PIPER_VOICE", "").strip()
    if not binary or not voice:
        return None
    output = settings.speech_dir / "jx_jarvis_piper.wav"
    process = subprocess.run(
        [binary, "--model", voice, "--output_file", str(output)],
        input=text,
        text=True,
        capture_output=True,
        timeout=45,
        check=False,
    )
    if process.returncode != 0:
        return {"ok": False, "spoken": False, "audioFile": None, "engine": "piper", "error": process.stderr.strip()}
    EdgeSpeaker().play(Path(output))
    return {"ok": True, "spoken": True, "audioFile": str(output), "engine": "piper"}

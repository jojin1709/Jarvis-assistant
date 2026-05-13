from __future__ import annotations

from pathlib import Path
from typing import Iterable

from providers.config import load_provider_config
from voice.recognizer import VoiceRecognizer


class SpeechToTextEngine:
    def __init__(self) -> None:
        self.recognizer = VoiceRecognizer()

    def transcribe_once(self, duration: float = 6, language: str = "auto") -> dict:
        transcript = self.recognizer.listen_once(duration=duration, language_mode=language)
        return {"ok": bool(transcript), "transcript": transcript, "engine": self.active_engine()}

    def transcribe_file(self, audio_path: str | Path, language: str = "auto") -> dict:
        path = Path(audio_path)
        provider_config = load_provider_config()
        model_name = str(provider_config.get("models", {}).get("faster_whisper") or "base")

        try:
            from faster_whisper import WhisperModel

            model = WhisperModel(model_name, device="auto", compute_type="int8")
            segments, info = model.transcribe(str(path), vad_filter=True, language=None if language == "auto" else language)
            text = " ".join(segment.text.strip() for segment in segments).strip()
            return {"ok": bool(text), "transcript": text, "engine": "faster-whisper", "language": getattr(info, "language", language)}
        except ImportError:
            pass
        except Exception as error:
            return {"ok": False, "transcript": "", "engine": "faster-whisper", "error": str(error)}

        local = self.recognizer._transcribe_local_whisper(path, provider_config)
        return {"ok": bool(local), "transcript": local, "engine": "openai-whisper"}

    def stream_transcript(self, duration: float = 6, language: str = "auto") -> Iterable[dict]:
        yield {"type": "status", "message": "listening"}
        result = self.transcribe_once(duration=duration, language=language)
        yield {"type": "transcript", **result}

    def active_engine(self) -> str:
        config = load_provider_config()
        route = str(config.get("routes", {}).get("voice") or "").lower()
        if route:
            return route
        return "local-whisper" if str(config.get("models", {}).get("local_whisper") or "").strip() else "speech-recognition"

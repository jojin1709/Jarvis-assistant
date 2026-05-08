import asyncio
import time
from pathlib import Path

import edge_tts
from playsound import playsound

from api.sarvam_services import synthesize_sarvam_speech
from app.config import settings


class EdgeSpeaker:
    def __init__(self) -> None:
        self.voice = settings.voice_name
        self.output_dir = settings.speech_dir

    async def _save_async(self, text: str, output_path: Path, voice: str) -> None:
        communicate = edge_tts.Communicate(text=text, voice=voice, rate="+0%")
        await communicate.save(str(output_path))

    def synthesize(self, text: str, language: str = "en") -> Path:
        safe_time = int(time.time() * 1000)
        if settings.tts_provider in {"sarvam", "auto"} and settings.sarvam_api_key:
            output_path = self.output_dir / f"jx_jarvis_{safe_time}.wav"
            try:
                return synthesize_sarvam_speech(text, language, output_path)
            except Exception:
                if settings.tts_provider == "sarvam":
                    raise

        output_path = self.output_dir / f"jx_jarvis_{safe_time}.mp3"
        voice = settings.malayalam_voice_name if language == "ml" else self.voice
        try:
            asyncio.run(self._save_async(text, output_path, voice))
        except Exception:
            if voice == self.voice:
                raise
            asyncio.run(self._save_async(text, output_path, self.voice))
        return output_path

    def play(self, audio_path: Path) -> None:
        playsound(str(audio_path), block=True)

    def speak(self, text: str, language: str = "en") -> Path:
        audio_path = self.synthesize(text, language=language)
        self.play(audio_path)
        return audio_path

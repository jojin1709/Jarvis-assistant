import asyncio
import time
from pathlib import Path

import edge_tts
from playsound import playsound

from app.config import settings


class EdgeSpeaker:
    def __init__(self) -> None:
        self.voice = settings.voice_name
        self.output_dir = settings.speech_dir

    async def _save_async(self, text: str, output_path: Path) -> None:
        communicate = edge_tts.Communicate(text=text, voice=self.voice, rate="+0%")
        await communicate.save(str(output_path))

    def synthesize(self, text: str) -> Path:
        safe_time = int(time.time() * 1000)
        output_path = self.output_dir / f"jx_jarvis_{safe_time}.mp3"
        asyncio.run(self._save_async(text, output_path))
        return output_path

    def play(self, audio_path: Path) -> None:
        playsound(str(audio_path), block=True)

    def speak(self, text: str) -> Path:
        audio_path = self.synthesize(text)
        self.play(audio_path)
        return audio_path

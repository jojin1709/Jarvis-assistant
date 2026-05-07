import speech_recognition as sr
import sounddevice as sd

from app.config import settings


def _looks_malayalam(text: str) -> bool:
    return any("\u0D00" <= char <= "\u0D7F" for char in text)


class VoiceRecognizer:
    def __init__(self) -> None:
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 320
        self.recognizer.dynamic_energy_threshold = True

    def listen_once(self, duration: int = 6, sample_rate: int = 16000) -> str:
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
        )
        sd.wait()
        audio = sr.AudioData(recording.tobytes(), sample_rate, 2)

        transcripts: list[str] = []
        for language in settings.speech_languages:
            try:
                transcript = self.recognizer.recognize_google(audio, language=language)
                if transcript and transcript not in transcripts:
                    transcripts.append(transcript)
            except sr.UnknownValueError:
                continue
            except sr.RequestError as exc:
                return f"Speech recognition service error: {exc}"

        if transcripts:
            for transcript in transcripts:
                if _looks_malayalam(transcript):
                    return transcript
            return transcripts[0]

        try:
            return self.recognizer.recognize_google(audio, language="en-IN")
        except sr.UnknownValueError:
            return "I could not clearly understand the audio."
        except sr.RequestError as exc:
            return f"Speech recognition service error: {exc}"

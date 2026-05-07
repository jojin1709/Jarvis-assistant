import speech_recognition as sr
import sounddevice as sd

from app.config import settings


def _looks_malayalam(text: str) -> bool:
    return any("\u0D00" <= char <= "\u0D7F" for char in text)


def _best_google_result(result: dict) -> tuple[str, float] | None:
    alternatives = result.get("alternative", []) if isinstance(result, dict) else []
    if not alternatives:
        return None

    first = alternatives[0]
    transcript = str(first.get("transcript", "")).strip()
    confidence = float(first.get("confidence", 0.0) or 0.0)
    if not transcript:
        return None
    return transcript, confidence


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

        candidates: list[tuple[str, str, float]] = []
        for language in settings.speech_languages:
            try:
                result = self.recognizer.recognize_google(audio, language=language, show_all=True)
                best = _best_google_result(result)
                if best:
                    transcript, confidence = best
                    candidates.append((language, transcript, confidence))
            except sr.UnknownValueError:
                continue
            except sr.RequestError as exc:
                return f"Speech recognition service error: {exc}"

        if candidates:
            english = next((candidate for candidate in candidates if candidate[0].lower().startswith("en")), None)
            malayalam = next((candidate for candidate in candidates if candidate[0].lower().startswith("ml")), None)

            if english and not _looks_malayalam(english[1]):
                if not malayalam or not _looks_malayalam(malayalam[1]):
                    return english[1]
                if english[2] >= 0.55 or english[2] >= (malayalam[2] + 0.08):
                    return english[1]

            if malayalam and _looks_malayalam(malayalam[1]):
                return malayalam[1]

            return max(candidates, key=lambda candidate: candidate[2])[1]

        try:
            return self.recognizer.recognize_google(audio, language="en-IN")
        except sr.UnknownValueError:
            return "I could not clearly understand the audio."
        except sr.RequestError as exc:
            return f"Speech recognition service error: {exc}"

import speech_recognition as sr
import sounddevice as sd
import wave

from api.sarvam_services import transcribe_sarvam_audio
from app.config import settings
from providers.config import load_provider_config


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

    def listen_once(self, duration: int = 6, sample_rate: int = 16000, language_mode: str = "auto") -> str:
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
        )
        sd.wait()
        audio_bytes = recording.tobytes()
        audio_path = settings.speech_dir / "jx_jarvis_input.wav"
        with wave.open(str(audio_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_bytes)

        provider_config = load_provider_config()
        voice_provider = str(provider_config.get("routes", {}).get("voice") or settings.stt_provider).lower()

        if voice_provider == "local_whisper" or settings.stt_provider == "local_whisper":
            result = self._transcribe_local_whisper(audio_path, provider_config)
            if result:
                return result

        if settings.stt_provider in {"sarvam", "auto"} and settings.sarvam_api_key:
            try:
                return transcribe_sarvam_audio(audio_path)
            except Exception as error:
                if settings.stt_provider == "sarvam":
                    return f"Sarvam speech recognition error: {error}"

        audio = sr.AudioData(audio_bytes, sample_rate, 2)

        if language_mode == "en":
            languages = ("en-IN", "en-US")
        elif language_mode == "ml":
            languages = ("ml-IN",)
        else:
            languages = settings.speech_languages

        candidates: list[tuple[str, str, float]] = []
        for language in languages:
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

    def _transcribe_local_whisper(self, audio_path, provider_config: dict) -> str:
        model_name = str(provider_config.get("models", {}).get("local_whisper") or "base")
        try:
            import whisper
        except ImportError:
            return "Local Whisper is selected, but the whisper package is not installed."
        try:
            model = whisper.load_model(model_name)
            result = model.transcribe(str(audio_path), fp16=False)
        except Exception as error:
            return f"Local Whisper transcription failed: {error}"
        text = str(result.get("text") or "").strip()
        return text or "Local Whisper did not detect speech."

import speech_recognition as sr
import sounddevice as sd


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

        try:
            return self.recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return "I could not clearly understand the audio."
        except sr.RequestError as exc:
            return f"Speech recognition service error: {exc}"

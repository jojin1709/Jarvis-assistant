# Voice

The voice system is implemented in `backend/voice`.

Flow:

1. Wake mode listens for `Hey Jarvis` when the Wake control is on.
2. `SpeechRecognition` captures microphone input.
3. Recognized commands are sent to safe system actions or the Groq API.
4. `edge-tts` generates a realistic voice response.
5. `playsound` plays the generated audio on the desktop.

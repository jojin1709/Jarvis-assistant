# JX JARVIS Backend

Python Flask backend for microphone input, SpeechRecognition, Groq AI responses, Edge-TTS synthesis, audio playback, file intake, and safe local system actions.

Key endpoints:

- `POST /api/assistant/listen`
- `POST /api/assistant/wake-listen`
- `POST /api/assistant/chat`
- `POST /api/files/upload`
- `POST /api/system/task`

System actions are allowlisted. JX JARVIS does not execute arbitrary shell commands from chat.

Wake phrases:

- `hey jarvis`
- `hi jarvis`
- `hello jarvis`
- `ok jarvis`
- `okay jarvis`
- `jarvis`

Run directly:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py -3 -m app.main
```

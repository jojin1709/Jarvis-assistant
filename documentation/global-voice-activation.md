# Global Voice Activation

Jarvis now starts a background voice runtime with the backend and registers a system-wide Electron push-to-talk shortcut.

## Lifecycle

```text
Jarvis launch
  -> backend starts voice_runtime
  -> Electron registers Space+M
  -> tray keeps process alive
  -> hotkey triggers /api/voice/push-to-talk
  -> microphone capture
  -> STT transcription
  -> safety check
  -> cognitive command router
  -> workflow execution
  -> optional TTS response
```

## Hotkey

Primary shortcut:

```text
Space+M
```

If the operating system refuses that accelerator, Electron registers `Alt+M` as a fallback and notifies the user.

The shortcut is registered with Electron `globalShortcut`, so it works while Jarvis is visible, minimized, or hidden to tray.

## Tray Controls

The tray menu includes:

- Enable Voice
- Mute Jarvis
- Push-To-Talk Space+M
- Continuous Listening
- Push-To-Talk Mode
- Quit

Closing the window hides Jarvis to tray so voice can keep running. Use tray `Quit` to fully exit.

## STT And TTS

Speech-to-text is local-first:

- `faster-whisper` when installed
- local Whisper fallback when configured
- existing SpeechRecognition/Sarvam fallback routes

Text-to-speech supports:

- Piper when `PIPER_BINARY` and `PIPER_VOICE` are configured
- existing Edge/Sarvam TTS fallback
- silent mode

## API

```text
GET   /api/voice/runtime
PATCH /api/voice/runtime
GET   /api/voice/microphones
POST  /api/voice/push-to-talk
POST  /api/voice/interrupt
```

## Setup

```powershell
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Optional Piper:

```powershell
$env:PIPER_BINARY="C:\Tools\piper\piper.exe"
$env:PIPER_VOICE="C:\Tools\piper\voices\en_US-lessac-medium.onnx"
```

## Testing

```powershell
npm run test:backend
npm run build
```

Manual test:

1. Start Jarvis with `npm run dev`.
2. Hide Jarvis to tray.
3. Press `Space+M`.
4. Speak a command like `open downloads` or `build a React dashboard`.
5. Confirm the Voice page shows the transcript, status, and response.

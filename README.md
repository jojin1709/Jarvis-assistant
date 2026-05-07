# JX JARVIS

JX JARVIS is a futuristic Windows desktop AI assistant built with Electron, React, TailwindCSS, Framer Motion, Python, Groq, SpeechRecognition, and Edge-TTS.

It runs as a real desktop app, listens through your microphone, wakes up when you say `Hey Jarvis`, sends commands to Groq, speaks back with a realistic voice, and can run safe allowlisted Windows tasks.

## Features

- Real Windows desktop app with Electron
- Futuristic compact Jarvis-style interface
- Wake word mode: `Hey Jarvis`
- Push-to-talk microphone button
- Text command console
- Groq AI responses
- Edge-TTS voice output
- File upload and local file intake
- Safe Windows actions like opening Calculator, Explorer, YouTube, music, notes, and Desktop scan
- Code-writing commands that create a local workspace and open it in VS Code
- Persistent local memory for preferences you ask it to remember
- Safer file actions with confirmation before move, rename, or trash
- Packaging helpers for building a Windows installer
- Production build support with Electron Builder

## Important Security Note

Never commit your real API keys.

This project uses a local `.env` file for secrets. The real `.env` file is ignored by Git through `.gitignore`. Only `.env.example` is safe to upload.

If you ever pasted a real key into GitHub, immediately rotate that key in your Groq dashboard.

## Tech Stack

Frontend:

- React
- Vite
- TailwindCSS
- Framer Motion
- Lucide React icons

Desktop:

- Electron
- Electron Builder

Backend:

- Python
- Flask
- Waitress
- SpeechRecognition
- sounddevice
- Edge-TTS
- playsound

AI:

- Groq API

## Project Structure

```text
JX-JARVIS/
├── assets/
│   ├── icon.ico
│   ├── splash.png
│   └── sounds/
├── backend/
│   ├── api/
│   │   ├── file_ingest.py
│   │   ├── groq_ai.py
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── system_tasks.py
│   ├── app/
│   │   ├── config.py
│   │   └── main.py
│   ├── voice/
│   │   ├── recognizer.py
│   │   └── speaker.py
│   └── requirements.txt
├── electron/
│   ├── main.js
│   ├── preload.js
│   └── splash.js
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── lib/
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── scripts/
│   ├── build-backend.ps1
│   ├── generate-desktop-assets.ps1
│   ├── setup-backend.ps1
│   ├── start-backend.ps1
│   └── start-electron.js
├── .env.example
├── .gitignore
├── package.json
└── README.md
```

## Requirements

Install these before running the project:

- Windows 10 or Windows 11
- Node.js LTS
- Python 3.11 or newer
- A Groq API key
- A working microphone
- Internet connection for Groq, SpeechRecognition, and Edge-TTS

## Setup

### 1. Clone the repository

```powershell
git clone https://github.com/jojin1709/Jarvis-assistant.git
cd Jarvis-assistant
```

### 2. Install Node and Electron dependencies

```powershell
npm run install:all
```

### 3. Set up the Python backend

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-backend.ps1
```

### 4. Create your private environment file

```powershell
Copy-Item .env.example .env
```

Open `.env` and add your own Groq key:

```env
GROQ_API_KEY=your_real_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
JX_JARVIS_VOICE=en-US-GuyNeural
JX_JARVIS_MALAYALAM_VOICE=ml-IN-MidhunNeural
JX_JARVIS_SPEECH_LANGUAGES=en-IN,ml-IN
JX_JARVIS_OWNER_NAME=User
JX_JARVIS_BACKEND_PORT=8765
JX_JARVIS_ENABLE_SYSTEM_TASKS=true
```

Do not upload `.env` to GitHub.

## How To Get A Groq API Key

JX JARVIS uses Groq for AI replies. You need your own Groq API key before the assistant can answer AI commands.

1. Open the official Groq API Keys page:

```text
https://console.groq.com/keys
```

2. Sign up or log in to GroqCloud.
3. Click `Create API Key`.
4. Give the key a clear name, for example `JX JARVIS Desktop`.
5. Copy the key immediately. Groq will not show the full key again after you leave the page.
6. In this project, copy `.env.example` to `.env` if you have not already done it:

```powershell
Copy-Item .env.example .env
```

7. Open `.env` and paste your key here:

```env
GROQ_API_KEY=paste_your_real_groq_key_here
```

8. Save `.env`, then restart JX JARVIS.

Official Groq docs:

- API Keys: https://console.groq.com/keys
- Quickstart: https://console.groq.com/docs/quickstart
- Security guidance: https://console.groq.com/docs/production-readiness/security-onboarding

Security rules:

- Never paste your real API key into GitHub, screenshots, Discord, YouTube, or public chat.
- Never put the key inside frontend React code.
- Keep it only in `.env` for development or `%APPDATA%\JX JARVIS\.env` for the installed app.
- If a key is leaked, revoke it in GroqCloud and create a new one.

## Privacy And Local Files

This repository should contain only the files needed to build and run JX JARVIS on another computer.

These files stay local and are ignored by Git:

- `.env` and all real API keys
- Generated voice audio in `backend/runtime/speech/`
- Uploaded files in `backend/runtime/uploads/`
- Saved local memory in `backend/runtime/memory.json`
- Generated code projects in `JX-JARVIS-Code/`
- Local trash/staging folders such as `JX-JARVIS-Trash/`
- Personal startup audio such as `assets/sounds/startup.wav`, `assets/sounds/startup.mp3`, or root `startup.*`
- Local downloaded reference images such as `ChatGPT Image*`

Before pushing, run:

```powershell
git status
```

Only commit source code, safe example files, docs, and public assets. Do not commit personal files, secrets, generated speech, uploads, or private media.

## User Name And Local Memory

JX JARVIS does not ship with your personal name, interests, or saved memories. Each person who clones the repo gets their own local memory file at `backend/runtime/memory.json`, and that file is ignored by Git.

Ways to set the current user's name:

```env
JX_JARVIS_OWNER_NAME=YourName
```

Or tell Jarvis:

```text
my name is Alex
call me Alex
remember my interest is web development
what do you remember
clear memory
```

If no name is configured or remembered, Jarvis uses the current computer account name when possible, otherwise it says `User`.

## Run The Desktop App

```powershell
npm run dev
```

This starts:

- React/Vite dev server on `127.0.0.1:5173`
- Electron desktop window
- Python backend on `127.0.0.1:8765`

The app opens in its own desktop window. You do not need to open a browser tab.

## How To Use

Wake word:

```text
Hey Jarvis
ജാർവിസ്
```

One-shot commands:

```text
Hey Jarvis, what time is it
Hey Jarvis, open YouTube
Hey Jarvis, open calculator
ജാർവിസ്, യൂട്യൂബ് തുറക്കൂ
ജാർവിസ്, സമയം എത്രയാണ്
ജാർവിസ്, snake game website ഉണ്ടാക്കൂ
Hey Jarvis, search Google for React Electron desktop app
Hey Jarvis, search YouTube for Python projects
Hey Jarvis, open Chrome
Hey Jarvis, remember that I prefer React
Hey Jarvis, write code for a calculator website
Hey Jarvis, create a Python script to organize downloads
```

Push-to-talk:

1. Click `Speak`.
2. Say your command.
3. Wait for JX JARVIS to respond.

Text command:

1. Type in the command line at the bottom.
2. Press Enter or click send.

File upload:

1. Click `Upload`.
2. Select a text, code, image, audio, video, PDF, CSV, JSON, or Markdown file.
3. JX JARVIS stores it locally and summarizes supported text-like files.

## Supported Local Commands

```text
open calculator
open notepad
open explorer
open youtube
open google
open gmail
open github
open whatsapp
open chrome
open edge
take screenshot
play music
list desktop
system status
create note
create folder Projects on desktop
open file resume
move file report to documents
rename file old-name to new-name
delete file temp
remember that I like Python
what do you remember
what time is it
what date is it
find file README
search desktop for video
search google for Groq API
search youtube for React tutorial
open VS Code
write code for a todo app
open latest code
test latest code
```

Generated code projects are saved on your Desktop in:

```text
JX-JARVIS-Code/
```

Move, rename, and delete commands ask for a confirmation token before they run. Delete moves the item into `Desktop\JX-JARVIS-Trash` instead of permanently deleting it.

## Safety Model

JX JARVIS does not run arbitrary shell commands from chat.

Local system actions are allowlisted in:

```text
backend/api/system_tasks.py
```

To disable local desktop actions, set this in `.env`:

```env
JX_JARVIS_ENABLE_SYSTEM_TASKS=false
```

## Build For Production

Build the frontend:

```powershell
npm run build:frontend
```

Build the Python backend executable:

```powershell
npm run build:backend
```

Create a Windows installer:

```powershell
npm run dist
```

Or double-click:

```text
Package JX JARVIS.bat
```

The installer is created in:

```text
release/JX JARVIS-Setup-1.0.0.exe
```

The `release/` folder is ignored by Git because installers and build output should not be committed.

## Using Secrets In The Installed App

For development, place `.env` in the project root.

For the installed Windows app, create this file:

```text
%APPDATA%\JX JARVIS\.env
```

Example full path:

```text
C:\Users\<your-name>\AppData\Roaming\JX JARVIS\.env
```

Put your Groq key there using the same format as `.env.example`.

## Troubleshooting

Backend offline:

- Run `npm run backend` to see backend logs.
- Make sure port `8765` is free.
- Make sure Python dependencies installed successfully.

No microphone input:

- Enable microphone access in Windows Settings.
- Check your default input device.
- Try running the app as a normal desktop app, not inside a restricted terminal.

No Groq response:

- Check that `.env` exists.
- Check that `GROQ_API_KEY` is valid.
- Restart the app after editing `.env`.

No voice output:

- Check Windows sound output.
- Make sure Edge-TTS has internet access.
- Make sure `playsound` installed correctly.

Electron opens but backend does not respond:

- Run `npm run backend`.
- In another terminal, run `npm run electron`.
- Check whether another app is using port `8765`.

## GitHub Upload Guide

If this folder is not a Git repository yet:

```powershell
git init
git branch -M main
git remote add origin https://github.com/jojin1709/Jarvis-assistant.git
git add .
git commit -m "Initial JX JARVIS desktop assistant"
git push -u origin main
```

Before pushing, check what will be committed:

```powershell
git status
```

Make sure these are not listed:

```text
.env
node_modules/
frontend/node_modules/
backend/.venv/
backend-dist/
release/
backend/runtime/uploads/
backend/runtime/speech/
```

## Contributing

Helpful improvements are welcome:

- Better wake-word detection
- More UI themes
- More safe local actions
- Better offline speech recognition
- Better file understanding
- Installer improvements

Please keep API keys, local files, generated audio, installers, and personal data out of pull requests.

## License

MIT License. See `LICENSE`.

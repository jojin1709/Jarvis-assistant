# JX Jarvis

**Autonomous AI Desktop Operating System**

JX Jarvis is a premium Windows desktop AI assistant created by **Jojin John**. It combines voice control, AI chat, browser automation, desktop actions, coding workflows, local memory, permissions, and multi-provider AI routing into one Electron desktop workspace.

Creator: [Jojin John](https://www.linkedin.com/in/jojin-john-74386b34a)

## What Jarvis Does

JX Jarvis is built to do real work, not just reply with text.

- Wake with "Hey Jarvis" or use manual voice/text commands.
- Open and control desktop apps.
- Run safe system actions.
- Automate a visible browser with Playwright.
- Search Google and YouTube visually.
- Generate websites and local code projects.
- Analyze projects and run build scripts.
- Store local memory, conversations, workflows, and preferences.
- Protect sensitive folders, files, apps, and actions with permissions.
- Switch between cloud AI and local/offline AI providers.
- Route AI work through logged-in ChatGPT, Claude, and Gemini browser sessions.
- Show live thinking, planning, execution logs, retries, and verification.

## Documentation Website

Read the live JX Jarvis documentation here:

https://jojin1709.github.io/Jarvis-assistant/

The documentation includes installation, first-time setup, voice, browser automation, AI providers, memory, permissions, workflows, plugin system, and developer guide pages.

For the newest platform changes, see [documentation/latest-upgrade-summary.md](documentation/latest-upgrade-summary.md).

## Core Features

### Autonomous OS Layer

Jarvis now includes a modular autonomous execution layer:

- Planner/task graph engine with optional LangGraph adapter.
- Specialized agents for planning, coding, browser work, recon, reports, memory, and DevOps.
- Secure queued terminal execution with command history, cancellation, stdout/stderr capture, and safety policy checks.
- Self-healing full-stack coding loop for MERN-style projects.
- Bug bounty recon workflow that chains locally installed tools and exports Markdown reports.
- SQLite memory with deterministic local embeddings for project, workflow, conversation, and report recall.

See [documentation/autonomous-os-architecture.md](documentation/autonomous-os-architecture.md) for architecture details.

### Autonomous Multimodal Workstation

Jarvis now has a unified world-state layer that connects screen vision, browser state, terminal jobs, workflow graphs, scheduler tasks, provider status, knowledge search, execution telemetry, and agent messages into one operating dashboard.

New integrated systems include:

- OCR-backed screenshot analysis and UI/popup detection.
- Permission-checked desktop automation.
- Graph workflow builder/runtime with recurring scheduler support.
- SQLite knowledge base with `sentence-transformers` semantic embeddings when available, plus a deterministic local fallback for unsupported Python runtimes.
- Behavior learning and execution quality scoring.
- Docker sandbox execution for generated code and tools.
- Internet research helpers and live codebase mapping.
- Agent message bus, decision engine, self-improvement analytics, and mobile companion notification state.

See [documentation/autonomous-multimodal-workstation.md](documentation/autonomous-multimodal-workstation.md) for API and setup details.

### Unified Autonomous Platform

Jarvis now has a central intelligence layer that joins the agents into one operating platform rather than disconnected tools. The platform stores active task state, execution history, failure memory, service capabilities, selected strategy, context digest, agent messages, and recent task outcomes.

Core flow:

```text
Goal -> intelligence snapshot -> task graph -> agent execution loop -> retry/self-heal -> memory/dashboard
```

See [documentation/unified-autonomous-platform.md](documentation/unified-autonomous-platform.md) for the orchestration model and execution diagrams.

### Agentic Cognitive Loop

Jarvis now runs platform goals through a structured cognitive loop:

```text
understand -> retrieve context -> plan -> coordinate agents -> execute -> observe -> reflect -> adapt -> retry safely -> remember
```

The loop adds reasoning plans, execution reviews, strategy optimization, failure classification, adaptive retry decisions, agent coordination events, and memory retrieval to normal autonomous execution.

See [documentation/agentic-cognitive-architecture.md](documentation/agentic-cognitive-architecture.md) for lifecycle details.

### Complete Autonomous Operating Platform

The latest core layer adds runtime environment awareness, crash-safe checkpoints, event-driven execution, a formal execution state machine, dry-run simulation, distributed worker queues, internal skills, marketplace registries, explainability, recovery planning, and resource optimization.

See [documentation/complete-autonomous-operating-platform.md](documentation/complete-autonomous-operating-platform.md) for the full core architecture and API list.

### Production Platform Finalization

Jarvis now includes optional user-owned cloud sync, encrypted local backup bundles, production telemetry controls, legal consent management, release security helpers, generated docs, community registry readiness, remote-worker architecture, and a polished production runtime panel.

Cloud sync is local-first and optional. It supports Google Drive, Dropbox, and OneDrive OAuth configuration without requiring centralized Jarvis cloud infrastructure. Jarvis never syncs raw browser cookies, plaintext credentials, `.env` files, virtual environments, or provider key stores.

See [documentation/production-platform-finalization.md](documentation/production-platform-finalization.md) for sync, release, installer, update, and deployment lifecycle details.

### Voice Assistant

- Wake words: `Hey Jarvis`, `Jarvis`
- Global push-to-talk hotkey: `Space+M`
- Background voice runtime starts when Jarvis launches
- Tray controls for voice enable/disable, mute, push-to-talk, and continuous listening
- English and Malayalam support
- Manual voice activation
- Background listening controls
- Edge TTS, Sarvam TTS, and local voice routing hooks
- Local Whisper route support when the dependency is installed

See [documentation/global-voice-activation.md](documentation/global-voice-activation.md) for the hotkey, tray, STT/TTS, and background runtime lifecycle.

### Visual Browser Automation

- Real visible Playwright browser
- Google search automation
- YouTube search automation
- Website opening and navigation
- Click-by-text actions
- Scrolling
- Page summaries
- Live screenshots, current URL, DOM summary, tabs, and browser logs

### Autonomous Execution Engine

- Understands user commands
- Creates execution plans
- Routes steps to tools
- Shows live thinking timeline
- Supports pause, resume, and cancel
- Retries recoverable failures
- Verifies results before reporting success

### Desktop Control

Jarvis can safely launch and control mapped local apps such as:

- Chrome
- Edge
- VS Code
- File Explorer
- Terminal
- Notepad
- Calculator
- YouTube, Google, GitHub, Gmail, WhatsApp web fallbacks

### Coding Agent

- Creates local code projects
- Generates portfolio and website projects
- Opens projects in VS Code
- Analyzes project structure
- Runs npm scripts when permitted
- Stores project memory for later sessions

### Memory System

Jarvis asks where to store its local brain during onboarding.

Memory structure:

```text
JarvisMemory/
  conversations/
  workflows/
  projects/
  preferences/
  voice/
  browser/
  automation/
  cache/
  embeddings/
  logs/
  backups/
  brain.sqlite3
```

Memory stays local unless the user explicitly exports it.

### Security and Permissions

Jarvis includes a permission system inspired by desktop privacy settings.

Controls include:

- Full System Access
- Safe Mode
- Auto Execution Mode
- File System Access
- Browser Control
- Terminal Execution
- App Control
- Voice Activation
- Automation Mode
- Internet Access
- Background Listening
- Protected folders, files, and apps
- Allowed workspaces
- Action confirmation levels
- Live action monitor

Jarvis must not bypass protected areas or fake successful actions.

### Multi-AI Provider System

Jarvis supports cloud, local, and hybrid AI routing.

Supported providers:

- Groq
- OpenAI
- Claude / Anthropic
- Gemini
- OpenRouter
- Ollama
- local llama.cpp OpenAI-compatible server
- Local Whisper for voice transcription
- Sarvam, DeepSeek, and NVIDIA compatibility from earlier integrations

Provider settings include:

- API key management
- Secure local key storage
- Provider enable/disable
- Test connection
- Current model
- Task routing for chat, coding, vision, voice, and automation
- Offline mode
- Hybrid failover
- Temperature and token settings

### AI Provider Orchestration Layer

Jarvis can use AI websites through Playwright browser automation with persistent local profiles:

- ChatGPT Web
- Claude Web
- Gemini Web
- Ollama, llama.cpp, DeepSeek, Qwen, and Llama-compatible local fallback through the existing local provider routes

The orchestration layer supports task routing, provider fallback, parallel multi-provider prompting, source-tracked response aggregation, prompt history, provider timing logs, and manual login recovery. It does not store web credentials, bypass captchas, automate account creation, or evade provider protections.

See [documentation/ai-provider-orchestration.md](documentation/ai-provider-orchestration.md) for setup.

## Tech Stack

Frontend:

- React
- Vite
- Zustand
- React Router
- Framer Motion
- Lucide icons

Desktop:

- Electron
- Electron Builder
- Tray mode
- Global shortcuts
- Native folder picker
- Splash screen with startup audio

Backend:

- Python
- Flask
- Waitress
- SQLite
- Playwright
- SpeechRecognition
- sounddevice
- Edge TTS

AI and Automation:

- Groq SDK
- OpenAI-compatible provider layer
- Anthropic Claude API
- Gemini API
- OpenRouter API
- Ollama local API
- llama.cpp local API
- Playwright visual browser operator

## Project Structure

```text
JX-JARVIS/
  assets/
  backend/
    agents/
    api/
    automation/
    browser/
    coding/
    execution/
    memory/
    plugins/
    profiles/
    providers/
    safety/
    system/
    tools/
    vision/
    voice/
  documentation/
    index.html
    docs/
    styles/
    scripts/
    assets/
    images/
    pages/
    videos/
  electron/
  frontend/
    src/
      components/
      hooks/
      layouts/
      overlays/
      pages/
      services/
      store/
      widgets/
      workflows/
  scripts/
  .env.example
  package.json
  README.md
```

## Requirements

- Windows 10 or Windows 11
- Node.js 20+
- Python 3.11 or 3.12 recommended for the full backend feature set
- Python 3.14 can run the core backend, but optional ML packages may be skipped
- Git
- Chrome or Microsoft Edge for visible browser automation
- Microphone access for voice features
- API key for at least one cloud provider, or Ollama/local model for offline AI

## Installation

Clone the repository:

```powershell
git clone https://github.com/jojin1709/Jarvis-assistant.git
cd Jarvis-assistant
```

Install Node dependencies:

```powershell
npm install
npm --prefix frontend install
```

Set up the Python backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
cd ..
```

`sentence-transformers` enables higher-quality semantic knowledge search on Python versions below 3.14. On Python 3.14, Jarvis falls back to deterministic local embeddings so the backend still starts cleanly.

Create your private environment file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and add your provider keys. Do not commit `.env`.

Install the Desktop shortcut:

```powershell
npm run install:desktop
```

This creates `Start JX JARVIS` on your Windows Desktop. Double-click it any
time to start Jarvis. On first launch, the shortcut launcher installs missing
Node/frontend dependencies, prepares the Python backend, and opens the desktop
app.

Run Jarvis:

```powershell
npm run dev
```

This starts:

- Vite frontend at `127.0.0.1:5173`
- Python backend at `127.0.0.1:8765`
- Electron desktop application

## Updating an Existing Install

If you already cloned JX Jarvis before, use these commands to get the latest
files from the official repository:

```powershell
cd Jarvis-assistant
git pull origin main
npm install
npm --prefix frontend install
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
backend\.venv\Scripts\python.exe -m playwright install chromium
npm run dev
```

Your private `.env` file is ignored by Git, so updating the repo will not upload
your API keys. If you edited source files locally, run `git status` before
pulling so you can save your own changes first.

## Environment Variables

Common provider keys:

```env
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GEMINI_API_KEY=your_gemini_key
OPENROUTER_API_KEY=your_openrouter_key
SARVAM_API_KEY=your_sarvam_key
DEEPSEEK_API_KEY=your_deepseek_key
NVIDIA_API_KEY=your_nvidia_key
```

Local AI:

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.1
LOCAL_LLAMACPP_BASE_URL=http://127.0.0.1:8080/v1
LOCAL_LLAMACPP_MODEL=local-model
```

Voice:

```env
JX_JARVIS_TTS_PROVIDER=edge
JX_JARVIS_STT_PROVIDER=google
JX_JARVIS_VOICE=en-US-GuyNeural
JX_JARVIS_MALAYALAM_VOICE=ml-IN-MidhunNeural
JX_JARVIS_SPEECH_LANGUAGES=en-IN,ml-IN
```

## Using Ollama

Install Ollama, then pull a model:

```powershell
ollama pull llama3.1
ollama serve
```

Open Jarvis:

```text
Settings -> AI Providers -> Ollama
```

Enable Ollama, select the model, and use Offline Mode if you want local-only responses.

## Common Commands

Voice examples:

```text
Hey Jarvis, open Chrome
Hey Jarvis, search Google for AI tools
Hey Jarvis, open YouTube and search cybersecurity tutorials
Hey Jarvis, create a beautiful portfolio website
Hey Jarvis, what do you remember?
```

Text examples:

```text
open VS Code
search google for latest AI news
open downloads and show system status
write code for a modern landing page
create a note on desktop
```

## Build

Build frontend:

```powershell
npm run build
```

Package app:

```powershell
npm run pack
```

Create Windows installer:

```powershell
npm run dist
```

The installer created by `npm run dist` also creates a Desktop shortcut and
Start Menu shortcut through Electron Builder.

## Privacy and Security

Never commit secrets.

Ignored local/private files include:

- `.env`
- `.env.*`
- `backend/.venv/`
- `node_modules/`
- `frontend/node_modules/`
- `backend/runtime/`
- generated speech files
- uploaded files
- local memory databases
- packaged builds
- generated installers

If any API key was pasted in public chat, screenshots, GitHub, or recordings, rotate that key in the provider dashboard.

## Development Checks

Compile backend:

```powershell
backend\.venv\Scripts\python.exe -m compileall backend
```

Build frontend:

```powershell
npm run build
```

Check Git status before pushing:

```powershell
git status
```

## Contributing

JX Jarvis is a source-available proprietary project created by Jojin John.
Public users do not have direct edit access to the official application files or
repository. Suggested changes must be submitted through pull requests and are
accepted only if reviewed and merged by Jojin John.

Good pull requests should:

- Keep changes focused.
- Avoid committing secrets or runtime data.
- Preserve permission checks for real actions.
- Avoid fake UI-only task execution.
- Include documentation updates for new tools, providers, or workflows.
- Verify backend compile and frontend build.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution rules.

## Ownership and License

JX Jarvis is owned by Jojin John. The source is visible for transparency,
learning, personal evaluation, and personal use, but it is not open-source
software.

You may not redistribute, sell, rebrand, publish modified builds, or claim this
project as your own without written permission from Jojin John.

See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).

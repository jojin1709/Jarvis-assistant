# AI Provider Orchestration Layer

Jarvis can route AI work through persistent browser sessions for ChatGPT, Claude, and Gemini, then fall back to API or local models when configured. This layer uses Playwright Chromium persistent contexts and does not store web credentials.

## Modules

- `backend/providers/base_provider.py` defines the shared browser provider contract, prompt submission, response extraction, timeout handling, and login-required detection.
- `backend/providers/chatgpt_provider.py` automates ChatGPT through a persistent Chromium profile.
- `backend/providers/claude_provider.py` keeps the existing Claude API provider and adds a Claude browser provider.
- `backend/providers/gemini_provider.py` keeps the existing Gemini API provider and adds a Gemini browser provider.
- `backend/providers/local_provider.py` keeps the local OpenAI-compatible provider and adds a router-friendly local provider adapter.
- `backend/providers/session_manager.py` owns Playwright, browser profiles, kept login sessions, and provider event logs.
- `backend/providers/provider_router.py` selects providers by task type, runs fallbacks, supports parallel multi-provider prompting, aggregates responses, and records prompt history.

## Persistent Profiles

Browser state is stored locally and ignored by git:

```text
backend/profiles/
  chatgpt/
  claude/
  gemini/
```

These folders preserve cookies, login sessions, and provider settings. They should never be committed or shared.

## Setup

Install Python dependencies and Chromium:

```powershell
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
backend\.venv\Scripts\python.exe -m playwright install chromium
```

Start Jarvis:

```powershell
npm run dev
```

Open `Settings > AI Provider Orchestration`, enable browser routing, enable the providers you want, then click `Open login` for each provider. Sign in manually in the visible browser window. Jarvis reuses that profile afterward.

## Routing

Default task routes:

```text
chat       -> ChatGPT Web
coding     -> Claude Web
reasoning  -> ChatGPT Web
research   -> Gemini Web
automation -> ChatGPT Web
```

If `Multi-provider mode` is enabled, Jarvis prompts enabled browser providers in parallel and returns a source-tracked merged response. If browser orchestration is unavailable and `Fallback to API/local` is enabled, normal API/local routing continues.

## Safety

This layer does not:

- bypass captchas
- evade anti-bot systems
- automate account creation
- store plaintext web credentials
- expose profile folders through the UI

If a provider logs out, Jarvis returns a login-required response and asks the user to reopen the login session manually.

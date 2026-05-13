# JX Jarvis Autonomous OS Architecture

JX Jarvis now keeps the existing desktop assistant UI and Flask API while adding a modular autonomous execution layer.

## Runtime Modules

- `backend/planner/` creates task graphs and execution state.
- `backend/agents/` contains specialized agents: planner, coding, browser, recon, report, memory, and DevOps.
- `backend/terminal/` provides queued terminal execution, command history, cancellation, stdout/stderr capture, and safety enforcement.
- `backend/workspace/` indexes project files, dependencies, scripts, and frameworks.
- `backend/workflows/` contains higher-level workflows such as bug bounty recon.
- `backend/reports/` generates structured Markdown vulnerability reports.
- `backend/memory/` and `backend/api/memory_storage.py` persist conversations, workflows, projects, reports, and local embeddings in SQLite.
- `backend/browser/` and `backend/api/browser_automation.py` provide Playwright browser operation.
- `backend/providers/` provides API/local model routing plus browser-based ChatGPT, Claude, and Gemini orchestration with persistent profiles.

## AI Provider Orchestration

Jarvis can now ask AI websites through a visible Playwright browser session when browser routing is enabled in Settings. The router maps task classes to providers, keeps provider profiles under `backend/profiles/`, records prompt/response history, and can run multi-provider prompting in parallel.

Default routes:

- Coding tasks use Claude Web first.
- Reasoning and automation tasks use ChatGPT Web first.
- Research tasks use Gemini Web first.
- API and local providers remain available as fallback when enabled.

See [ai-provider-orchestration.md](ai-provider-orchestration.md) for setup and safety details.

## Autonomous Coding Loop

For MERN/full-stack goals, Jarvis:

1. Builds a task graph.
2. Creates a project workspace under `Desktop/JX-JARVIS-Code`.
3. Writes frontend and backend files.
4. Runs dependency installation through the terminal engine.
5. Runs frontend/backend verification commands.
6. Applies known self-healing patches for common build/runtime failures.
7. Opens a browser preview through the browser agent.
8. Stores project state and logs in memory.

## Bug Bounty Workflow

For authorized bug bounty targets, Jarvis:

1. Normalizes target scope.
2. Detects installed recon tools on `PATH`.
3. Runs available tools such as `subfinder`, `amass`, `httpx`, `gau`, `katana`, `nuclei`, and `trufflehog`.
4. Parses outputs for high-signal anomalies.
5. Writes a YesWeHack-style Markdown report.
6. Stores findings and report paths in memory.

## Safety Model

Terminal execution uses both the permissions system and command policy:

- Dangerous command patterns are blocked.
- Only development/security tool executables are allowed by the terminal service.
- Terminal execution must be enabled in Security & Permissions.
- Destructive filesystem operations still require confirmation.
- Recon workflows only run tools already installed locally and do not exploit targets.

## Setup

```powershell
npm install
npm --prefix frontend install
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
backend\.venv\Scripts\python.exe -m playwright install chromium
```

Optional security tools for recon:

```text
subfinder, amass, httpx, nuclei, ffuf, katana, gau, trufflehog, naabu
```

## Commands

```powershell
npm run dev
npm run build
npm run test:backend
```

Example Jarvis prompts:

```text
Build me a MERN restaurant website
Find bugs in example.com
Search memory for restaurant project
```

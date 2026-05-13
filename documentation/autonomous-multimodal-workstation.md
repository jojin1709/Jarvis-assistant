# Autonomous Multimodal Workstation

This upgrade connects Jarvis systems into a unified AI workstation that can reason across browser state, terminal activity, desktop UI, screenshots, workflows, memory, providers, and scheduled tasks.

## New Runtime Modules

- `backend/vision/` captures screenshots, runs OCR when available, detects UI/action text, identifies possible popups, and produces visual reasoning summaries.
- `backend/desktop/` provides permission-checked mouse, keyboard, clipboard, and active-window automation helpers.
- `backend/workflows/` now includes graph workflow validation, storage, node execution, and a visual-builder-ready folder.
- `backend/scheduler/` runs recurring workflow definitions in the background.
- `backend/knowledge/` stores indexed documents in SQLite with deterministic local embeddings and semantic search.
- `backend/learning/` records user/provider/workflow behavior and scores preferences.
- `backend/sandbox/` runs commands inside Docker with no network, CPU/memory limits, and permission checks when Docker is available.
- `backend/research/` searches the web, fetches articles, summarizes text, and inspects GitHub repository metadata.
- `backend/workspace/code_map.py` builds dependency, import, package, and service maps.
- `backend/agents/message_bus.py` records agent-to-agent task messages for orchestration visibility.
- `backend/decision_engine/` selects strategy, provider, retry plan, and workflow optimization advice.
- `backend/self_improvement/` scores execution quality and generates retry recommendations from failures.
- `backend/mobile_companion/` stores notification and remote-monitoring state for a future mobile app.
- `backend/context/` builds the multimodal world state and reasons over it.
- `backend/observability/` exposes telemetry for the dashboard.

## Key API Endpoints

```text
GET  /api/dashboard
POST /api/context/multimodal
POST /api/desktop/action
GET  /api/workflows/graphs
POST /api/workflows/graphs
POST /api/workflows/graphs/<id>/run
GET  /api/scheduler
POST /api/scheduler
GET  /api/knowledge/search?q=...
POST /api/knowledge/index
GET  /api/research/search?q=...
POST /api/research/summarize
GET  /api/workspace/code-map?path=...
POST /api/sandbox/run
GET  /api/self-improvement
GET  /api/agents/messages
GET  /api/mobile/state
```

## Optional Native Dependencies

```powershell
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

For best local operation, also install:

- Docker Desktop for sandbox execution.
- Tesseract OCR binary for OCR text extraction.
- A desktop session with UI automation access for `pyautogui`.

## Safety Model

Desktop and sandbox actions pass through the existing permission system. Docker sandbox runs with no network and resource limits. Login and credential entry remain manual.

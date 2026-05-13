# Unified Autonomous AI Operating Platform

Jarvis now uses a central platform layer so engineering, cybersecurity, browser automation, desktop automation, DevOps, research, workflows, memory, providers, and vision operate as one system.

## Orchestration Model

```text
User goal / voice command
        |
        v
Unified Intelligence Snapshot
  - multimodal context
  - service catalog
  - user preferences
  - failure memory
  - provider strategy
        |
        v
Planner -> TaskGraph
        |
        v
Autonomous Execution Loop
  - dispatch step to agent
  - observe result
  - record platform state
  - plan retry/self-heal
  - continue or fail safely
        |
        v
Memory + Reports + Dashboard Telemetry
```

## Shared State

`backend/platform_core/` is the shared intelligence spine:

- `service_catalog.py` lists platform capabilities and maps goals to services.
- `state_store.py` persists active task, recent tasks, step history, and failure memory.
- `intelligence.py` builds a single snapshot from context, strategy, learning, service catalog, and history.
- `execution_loop.py` runs goals through the autonomous orchestrator with the snapshot attached.

Every orchestrated step records into the same platform state, so Jarvis can see what is running, what failed, what tools are available, and what strategy was selected.

## Unified Agents

```text
PlannerAgent   -> task graphs and classification
CodingAgent    -> project generation and self-healing
BrowserAgent   -> Playwright browser automation
DesktopAgent   -> mouse, keyboard, clipboard, active windows
VisionAgent    -> screenshots, OCR, UI/popup detection
ResearchAgent  -> web search and summaries
ReconAgent     -> bug bounty/security tool chains
ReportAgent    -> vulnerability and Markdown reports
DevOpsAgent    -> terminal, builds, Docker/environment status
WorkflowAgent  -> reusable workflow graphs
MemoryAgent    -> execution and project memory
```

Agents communicate through `backend/agents/message_bus.py` and share state through `platform_core/state_store.py`.

## Execution Flow

```text
1. Goal enters /api/platform/execute or /api/agent/execute.
2. Jarvis builds an intelligence snapshot.
3. Planner creates a task graph.
4. Orchestrator dispatches ready steps to agents.
5. Each step result is written to:
   - task graph
   - agent message bus
   - platform history
   - memory, when appropriate
6. Retry planner classifies failures:
   - self_heal
   - provider_fallback
   - network_retry
   - request_approval
7. Final result and artifact keys are stored as a platform task.
```

## Platform APIs

```text
GET  /api/dashboard
POST /api/platform/intelligence
POST /api/platform/execute
GET  /api/agents/messages
GET  /api/self-improvement
```

The dashboard endpoint returns:

- multimodal world state
- telemetry and execution quality
- agent messages
- workflow/scheduler state
- platform active/recent tasks
- service catalog intelligence

## Deployment

Development:

```powershell
npm install
npm --prefix frontend install
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
backend\.venv\Scripts\python.exe -m playwright install chromium
npm run dev
```

Production build:

```powershell
npm run build
npm run package
```

Optional capabilities:

- Docker Desktop for sandbox and DevOps service inspection.
- Tesseract OCR binary for stronger OCR.
- Security tools on PATH for recon workflows: `subfinder`, `amass`, `httpx`, `nuclei`, `ffuf`, `katana`, `gau`, `trufflehog`, `naabu`.

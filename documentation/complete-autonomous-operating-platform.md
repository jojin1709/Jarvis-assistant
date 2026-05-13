# Complete Autonomous AI Operating Platform

Jarvis now has a unified cognitive core that coordinates runtime awareness, planning, execution, reflection, events, recovery, skills, simulation, learning, and optimization. The system remains practical and bounded: it does not claim AGI or consciousness, and high-risk actions still require safety checks and approvals.

## Cognitive Core

```text
backend/core/
  cognitive_core.py        # status and goal preparation
  contextual_brain.py      # intelligence + runtime + memory context
  reasoning_controller.py  # cognitive plan or dry run
  orchestration_engine.py  # coordination + skill selection
  execution_manager.py     # safety, checkpoints, state transitions, execution
  autonomous_runtime.py    # public runtime entrypoint
```

Execution flow:

```text
goal
  -> contextual brain
  -> cognitive plan
  -> skill + agent coordination
  -> safety governance
  -> checkpoint
  -> state machine EXECUTING
  -> cognitive execution loop
  -> reflection + learning
  -> event log + recovery state
```

## Runtime Awareness

```text
backend/environment/
  system_monitor.py
  gpu_monitor.py
  network_monitor.py
  process_tracker.py
  container_tracker.py
  runtime_analyzer.py
```

Jarvis monitors CPU, RAM, disk, GPU when available, network connectivity, active ports, processes, and Docker containers. The optimization layer uses this to reduce parallelism or prefer local/offline execution under pressure.

## Persistent Continuation And Recovery

```text
backend/persistence/
backend/recovery/
```

Jarvis writes checkpoints before autonomous execution and exposes recovery candidates. Rollback execution is approval-gated; rollback plans are generated without destructive action.

## State Machine And Events

```text
backend/state_machine/
backend/events/
```

Execution states:

```text
IDLE -> PLANNING -> EXECUTING -> OBSERVING -> REFLECTING -> RETRYING
WAITING -> RECOVERING -> COMPLETED / FAILED
```

Events such as `task_received`, `task_checkpointed`, `workflow_completed`, `workflow_failed`, and `security_alert` are written to runtime event logs and mirrored into platform history.

## Learning, Skills, Marketplace

```text
backend/learning/
backend/skills/
backend/marketplace/
```

Jarvis records workflow/tool/strategy outcomes, selects internal skills by goal, and exposes local skill/workflow marketplace registries for future downloadable packages.

## Simulation And Testing

```text
backend/simulation/
backend/testing/
```

Dry-run mode builds a cognitive plan, estimates impact, and previews commands without executing. Testing helpers suggest build/test commands, validate workflows, and verify execution results.

## Distributed Execution

```text
backend/distributed/
```

Jarvis now has a local JSON distributed queue, worker status, Docker coordination, and remote-task adapter hooks. Remote execution is queued until a worker backend is configured.

## Explainability

```text
backend/explainability/
```

Jarvis can explain reasoning traces, decisions, workflow structure, and action history through platform history and event logs.

## APIs

```text
GET  /api/core/status
POST /api/core/prepare
POST /api/core/dry-run
POST /api/platform/execute   {"goal": "...", "dryRun": true}
GET  /api/events
GET  /api/explainability/action-trace
GET  /api/skills
GET  /api/marketplace
GET  /api/distributed/workers
```

## Setup

```powershell
npm install
npm --prefix frontend install
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
backend\.venv\Scripts\python.exe -m playwright install chromium
npm run dev
```

Optional:

- Docker Desktop for sandbox/distributed Docker execution.
- NVIDIA drivers and `nvidia-smi` for GPU metrics.
- Tesseract OCR for stronger screenshot OCR.

## Verification

```powershell
npm run test:backend
npm run build
```

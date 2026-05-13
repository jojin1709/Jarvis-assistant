# Agentic Cognitive Architecture

Jarvis now has a practical cognitive execution loop layered over the existing autonomous platform. This does not claim consciousness or AGI; it is a structured reasoning and control system for planning, executing, observing, reflecting, and adapting.

## Cognitive Loop

```text
1. Understand goal
2. Retrieve memory/context
3. Analyze multimodal world state
4. Generate candidate strategies
5. Build a task graph
6. Coordinate agents
7. Execute agent steps
8. Observe outputs
9. Detect failures
10. Reflect and score execution
11. Adapt strategy and retry when safe
12. Store outcome in memory/platform state
```

## New Packages

```text
backend/reasoning/
  chain_of_thought.py       # inspectable reasoning summaries, not hidden model thoughts
  task_decomposer.py        # goal -> task graph
  strategy_generator.py     # candidate strategies
  contextual_reasoner.py    # context/risk/constraint analysis
  planning_engine.py        # combined cognitive plan
  execution_reasoner.py     # observations and continuation decisions

backend/reflection/
  failure_analyzer.py
  execution_reviewer.py
  strategy_optimizer.py
  retry_planner.py
  learning_engine.py

backend/orchestration/
  agent_bus.py
  shared_state.py
  task_router.py
  execution_graph.py
  coordination_manager.py

backend/memory/
  vector_memory.py
  episodic_memory.py
  semantic_memory.py
  workflow_memory.py
  memory_indexer.py
  context_retriever.py
```

## Agent Collaboration

```text
PlannerAgent
ReasoningAgent
CodingAgent
BrowserAgent
DesktopAgent
VisionAgent
ResearchAgent
ReconAgent
ReportAgent
WorkflowAgent
DevOpsAgent
MemoryAgent
ReflectionAgent
DecisionAgent
```

Agents exchange events through the message bus and share execution state through `platform_core/state_store.py`.

## Execution Lifecycle

```text
POST /api/platform/execute
        |
        v
build_intelligence_snapshot()
        |
        v
run_cognitive_execution_loop()
        |
        +--> build_cognitive_plan()
        +--> coordinate_goal()
        +--> execute_autonomous_goal()
        +--> review_execution()
        +--> decide_next_action()
        +--> learn_from_execution()
        |
        v
response + cognitivePlan + cycles + review + decision
```

## Safety Behavior

- Dangerous actions still pass through the existing permission system.
- Terminal actions remain policy checked.
- Sandbox execution uses Docker when available.
- Reflection can stop retries when approval, credential, login, or protected-resource signals appear.
- Memory write failures degrade safely and do not crash autonomous execution.

## Commands

```powershell
npm install
npm --prefix frontend install
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
backend\.venv\Scripts\python.exe -m playwright install chromium
npm run dev
```

Verification:

```powershell
npm run test:backend
npm run build
```

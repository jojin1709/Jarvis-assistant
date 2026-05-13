from __future__ import annotations


def architecture_markdown() -> str:
    return """# Jarvis Architecture

Jarvis is organized around a local-first cognitive core. Goals enter the API, pass through safety and context preparation, become execution graphs, then flow through agents, tools, memory, events, and recovery checkpoints.

Primary layers:
- core: cognition, orchestration, execution management
- agents: specialized task owners
- context/environment: world state and runtime awareness
- sync/telemetry/legal: optional production services
- workflows/skills/marketplace: reusable automation
"""

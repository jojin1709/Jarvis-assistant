from __future__ import annotations


def developer_guide_markdown() -> str:
    return """# Jarvis Developer Guide

1. Keep features local-first and optional by default.
2. Route autonomous actions through safety/governance checks.
3. Emit events for observable workflow transitions.
4. Store secrets with the secure store, never in plaintext config.
5. Add tests for new agent, workflow, sync, recovery, or release behavior.
"""

from __future__ import annotations

from workflows.workflow_store import list_workflow_definitions


def workflow_markdown() -> str:
    workflows = list_workflow_definitions()
    lines = ["# Jarvis Workflows", ""]
    for workflow in workflows:
        lines.append(f"- `{workflow.get('id')}`: {workflow.get('name', 'Unnamed workflow')}")
    return "\n".join(lines)

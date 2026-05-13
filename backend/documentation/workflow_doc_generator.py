from __future__ import annotations


def generate_workflow_doc(workflow: dict) -> str:
    lines = [f"# Workflow: {workflow.get('name') or workflow.get('id')}", "", "## Nodes"]
    for node in workflow.get("nodes", []):
        lines.append(f"- `{node.get('id')}`: {node.get('type')} - {node.get('label')}")
    lines.append("")
    lines.append("## Edges")
    for edge in workflow.get("edges", []):
        lines.append(f"- `{edge.get('from')}` -> `{edge.get('to')}`")
    return "\n".join(lines)

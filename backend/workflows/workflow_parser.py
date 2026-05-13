from __future__ import annotations


def normalize_workflow(payload: dict) -> dict:
    workflow = dict(payload or {})
    workflow.setdefault("id", _slug(workflow.get("name") or workflow.get("title") or "workflow"))
    workflow.setdefault("name", workflow["id"].replace("-", " ").title())
    workflow.setdefault("nodes", [])
    workflow.setdefault("edges", [])
    workflow["nodes"] = [_normalize_node(node, index) for index, node in enumerate(workflow.get("nodes") or [])]
    workflow["edges"] = [_normalize_edge(edge) for edge in workflow.get("edges") or []]
    return workflow


def validate_workflow(payload: dict) -> tuple[bool, str, dict]:
    workflow = normalize_workflow(payload)
    node_ids = {node["id"] for node in workflow["nodes"]}
    if not workflow["nodes"]:
        return False, "Workflow must contain at least one node.", workflow
    for edge in workflow["edges"]:
        if edge["from"] not in node_ids or edge["to"] not in node_ids:
            return False, f"Invalid edge {edge['from']} -> {edge['to']}.", workflow
    return True, "Workflow is valid.", workflow


def execution_order(workflow: dict) -> list[dict]:
    nodes = {node["id"]: node for node in workflow.get("nodes", [])}
    incoming = {node_id: set() for node_id in nodes}
    outgoing = {node_id: set() for node_id in nodes}
    for edge in workflow.get("edges", []):
        outgoing.setdefault(edge["from"], set()).add(edge["to"])
        incoming.setdefault(edge["to"], set()).add(edge["from"])
    ready = [node_id for node_id, deps in incoming.items() if not deps]
    ordered = []
    while ready:
        node_id = ready.pop(0)
        ordered.append(nodes[node_id])
        for child in sorted(outgoing.get(node_id, set())):
            incoming[child].discard(node_id)
            if not incoming[child]:
                ready.append(child)
    if len(ordered) != len(nodes):
        raise RuntimeError("Workflow graph contains a cycle.")
    return ordered


def _normalize_node(node: dict, index: int) -> dict:
    normalized = dict(node or {})
    normalized.setdefault("id", f"node-{index + 1}")
    normalized.setdefault("type", "note")
    normalized.setdefault("label", normalized["type"].replace("_", " ").title())
    normalized.setdefault("config", {})
    return normalized


def _normalize_edge(edge: dict) -> dict:
    return {"from": str(edge.get("from") or edge.get("source") or ""), "to": str(edge.get("to") or edge.get("target") or "")}


def _slug(value: str) -> str:
    import re

    slug = re.sub(r"[^a-zA-Z0-9]+", "-", str(value).strip().lower()).strip("-")
    return slug or "workflow"

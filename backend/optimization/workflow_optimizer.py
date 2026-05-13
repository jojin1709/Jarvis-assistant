from __future__ import annotations


def optimize_workflow_graph(workflow: dict, metrics: dict | None = None) -> dict:
    nodes = workflow.get("nodes") or []
    heavy = [node for node in nodes if node.get("type") in {"browser", "terminal", "docker", "model"}]
    recommendations = []
    if len(heavy) > 2:
        recommendations.append("Serialize heavy browser/terminal/model nodes or use agent scheduler priority lanes.")
    if metrics and metrics.get("failureRate", 0) > 0.2:
        recommendations.append("Enable checkpointing before high-failure nodes.")
    return {"ok": True, "nodeCount": len(nodes), "heavyNodeCount": len(heavy), "recommendations": recommendations}

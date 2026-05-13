from __future__ import annotations


SERVICE_CATALOG = {
    "planner": {"agent": "planner", "capabilities": ["goal_decomposition", "tool_selection", "task_graphs"]},
    "coding": {"agent": "coding", "capabilities": ["app_generation", "refactor", "debug", "self_heal"]},
    "browser": {"agent": "browser", "capabilities": ["navigate", "inspect_dom", "forms", "screenshots"]},
    "desktop": {"agent": "desktop", "capabilities": ["mouse", "keyboard", "clipboard", "windows"]},
    "vision": {"agent": "vision", "capabilities": ["screen_capture", "ocr", "ui_detection", "popup_detection"]},
    "research": {"agent": "research", "capabilities": ["web_search", "article_summary", "github_analysis", "knowledge_index"]},
    "recon": {"agent": "recon", "capabilities": ["subdomain_recon", "http_probe", "nuclei", "report_findings"]},
    "report": {"agent": "report", "capabilities": ["markdown_reports", "bug_bounty_reports", "documentation"]},
    "devops": {"agent": "devops", "capabilities": ["terminal", "docker", "builds", "service_orchestration"]},
    "workflow": {"agent": "workflow", "capabilities": ["graph_execution", "scheduling", "conditional_nodes"]},
    "memory": {"agent": "memory", "capabilities": ["conversation_memory", "project_memory", "execution_history"]},
}


def catalog_snapshot() -> dict:
    return {"services": SERVICE_CATALOG, "capabilityCount": sum(len(item["capabilities"]) for item in SERVICE_CATALOG.values())}


def tools_for_goal(goal: str) -> list[str]:
    lowered = goal.lower()
    selected = []
    for name, spec in SERVICE_CATALOG.items():
        if any(capability.replace("_", " ") in lowered or capability in lowered for capability in spec["capabilities"]):
            selected.append(name)
    if "bug" in lowered or "vulnerab" in lowered or "recon" in lowered:
        selected.extend(["recon", "report", "research"])
    if "build" in lowered or "code" in lowered or "fix" in lowered:
        selected.extend(["coding", "devops", "browser"])
    if "browser" in lowered or "page" in lowered or "website" in lowered:
        selected.extend(["browser", "vision"])
    if "screen" in lowered or "click" in lowered or "desktop" in lowered:
        selected.extend(["vision", "desktop"])
    return list(dict.fromkeys(selected or ["planner", "devops", "memory"]))

from __future__ import annotations


AGENT_TOOL_MAP = {
    "coding": {"create_fullstack_project", "self_heal", "refactor", "debug_project"},
    "browser": {"open_preview", "navigate", "inspect_page", "browser_task"},
    "desktop": {"desktop_state", "clipboard_read", "clipboard_write", "mouse", "keyboard"},
    "vision": {"screen_understanding", "screenshot", "ocr"},
    "research": {"internet_research", "github_analysis", "summarize"},
    "recon": {"scope", "bug_bounty_recon", "analyze_findings"},
    "report": {"markdown_report", "documentation"},
    "workflow": {"list_workflows", "run_workflow", "create_basic_workflow"},
    "devops": {"install_dependencies", "verify_build", "general_execute", "environment_report", "docker_status"},
    "memory": {"remember_project", "remember_execution", "remember_findings"},
}


def route_step(step: dict) -> dict:
    tool = str(step.get("tool") or "")
    configured = str(step.get("agent") or "")
    if configured:
        return {"agent": configured, "reason": "Step already specifies an agent."}
    for agent, tools in AGENT_TOOL_MAP.items():
        if tool in tools:
            return {"agent": agent, "reason": f"Tool {tool} maps to {agent}."}
    return {"agent": "devops", "reason": "Defaulting to DevOps/general execution."}

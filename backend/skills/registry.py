from __future__ import annotations


SKILLS = {
    "coding.mern": {"category": "coding", "description": "Generate and verify MERN-style applications.", "agents": ["coding", "devops", "browser"]},
    "recon.web": {"category": "recon", "description": "Run authorized web recon and report findings.", "agents": ["recon", "report"]},
    "reporting.markdown": {"category": "reporting", "description": "Build structured Markdown reports.", "agents": ["report"]},
    "deployment.local": {"category": "deployment", "description": "Inspect environment and run local deployment checks.", "agents": ["devops"]},
    "browser.inspect": {"category": "browser", "description": "Navigate, inspect, and summarize browser state.", "agents": ["browser", "vision"]},
    "workflows.graph": {"category": "workflows", "description": "Create and run reusable graph workflows.", "agents": ["workflow"]},
}


def list_skills() -> dict:
    return {"skills": SKILLS}


def select_skills(goal: str) -> list[dict]:
    lowered = goal.lower()
    selected = []
    for skill_id, spec in SKILLS.items():
        if spec["category"] in lowered or any(token in lowered for token in skill_id.split(".")):
            selected.append({"id": skill_id, **spec})
    return selected or [{"id": "workflows.graph", **SKILLS["workflows.graph"]}]

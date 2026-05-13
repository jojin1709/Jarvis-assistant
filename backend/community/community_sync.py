from __future__ import annotations

from community.plugin_registry import public_plugins
from community.skill_marketplace import public_skills
from community.workflow_hub import public_workflows


def community_state() -> dict:
    return {"enabled": False, "workflows": public_workflows(), "plugins": public_plugins(), "skills": public_skills()}

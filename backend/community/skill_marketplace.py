from __future__ import annotations

from marketplace.skill_registry import marketplace_skills


def public_skills() -> dict:
    return {"enabled": False, "source": "local-registry", "skills": marketplace_skills()}

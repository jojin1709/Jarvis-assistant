from __future__ import annotations

from skills.registry import list_skills


def marketplace_skills() -> dict:
    return {"local": list_skills().get("skills", {}), "remoteEnabled": False}

from __future__ import annotations


def suggest_tests(project_map: dict) -> list[dict]:
    services = project_map.get("services") or []
    suggestions = []
    for service in services:
        scripts = service.get("scripts") or {}
        if "test" in scripts:
            suggestions.append({"path": service.get("path"), "command": "npm test", "reason": "Existing package test script."})
        elif "build" in scripts:
            suggestions.append({"path": service.get("path"), "command": "npm run build", "reason": "Build script can validate compilation."})
    return suggestions

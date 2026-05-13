from __future__ import annotations


def generate_api_doc(flask_app) -> str:
    lines = ["# API Routes", ""]
    for rule in sorted(flask_app.url_map.iter_rules(), key=lambda item: str(item)):
        methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))
        lines.append(f"- `{methods}` `{rule}`")
    return "\n".join(lines)

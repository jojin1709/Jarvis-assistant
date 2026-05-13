from __future__ import annotations

from flask import Flask


def api_markdown(app: Flask | None = None) -> str:
    routes = []
    if app:
        for rule in sorted(app.url_map.iter_rules(), key=lambda item: item.rule):
            methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))
            routes.append(f"- `{methods} {rule.rule}`")
    return "# Jarvis API\n\n" + "\n".join(routes)

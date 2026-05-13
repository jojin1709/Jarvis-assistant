from __future__ import annotations

from plugins.registry import list_plugins


def plugin_markdown() -> str:
    lines = ["# Jarvis Plugins", ""]
    for plugin in list_plugins():
        lines.append(f"- `{plugin.get('id')}`: {'enabled' if plugin.get('enabled') else 'disabled'}")
    return "\n".join(lines)

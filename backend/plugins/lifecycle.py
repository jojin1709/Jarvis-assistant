from __future__ import annotations

from plugins.registry import list_plugins, set_plugin_enabled


def plugin_lifecycle_state() -> dict:
    plugins = list_plugins()
    return {
        "plugins": plugins,
        "enabled": [plugin for plugin in plugins if plugin.get("enabled")],
        "sandboxing": "Plugins run through registered backend actions and permission checks.",
    }


def set_plugin_state(plugin_id: str, enabled: bool) -> dict:
    plugin = set_plugin_enabled(plugin_id, enabled)
    return {"ok": bool(plugin), "plugin": plugin}

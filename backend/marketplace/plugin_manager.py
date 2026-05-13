from __future__ import annotations

from plugins.lifecycle import plugin_lifecycle_state


def marketplace_plugins() -> dict:
    return plugin_lifecycle_state()

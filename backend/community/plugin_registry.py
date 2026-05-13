from __future__ import annotations

from marketplace.plugin_manager import marketplace_plugins


def public_plugins() -> dict:
    return {"enabled": False, "source": "local-registry", "plugins": marketplace_plugins()}

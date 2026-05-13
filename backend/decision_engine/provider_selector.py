from __future__ import annotations

from learning.behavior import recommend
from providers.config import load_provider_config


def select_provider(task_type: str, context: dict | None = None) -> dict:
    config = load_provider_config()
    browser = config.get("browser_providers", {})
    learned = recommend(f"provider:{task_type}")
    route = browser.get("routes", {}).get(task_type) or config.get("routes", {}).get(task_type) or "auto"
    if learned:
        route = learned
    if browser.get("enabled") and route in browser.get("enabled_providers", {}) and browser["enabled_providers"].get(route):
        return {"provider": route, "source": "browser", "reason": f"Selected browser route for {task_type}."}
    return {"provider": route, "source": "api_or_local", "reason": f"Selected configured route for {task_type}."}

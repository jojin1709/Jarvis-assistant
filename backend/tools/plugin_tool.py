from __future__ import annotations

import json
from typing import Any

from api.permissions import guard_action
from plugins.registry import list_plugins
from tools.app_launcher import launch_from_command
from tools.browser_tool import run_browser_command
from tools.terminal_tool import run_terminal_command


def run_plugin_command(text: str) -> str | None:
    normalized = _normalize(text)
    if not normalized:
        return None

    for plugin in list_plugins():
        if not plugin.get("enabled", True):
            continue
        for command in _command_entries(plugin):
            if not _matches(command, normalized):
                continue
            return _execute_command(plugin, command)

    return None


def _command_entries(plugin: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for item in plugin.get("commands", []) if isinstance(plugin.get("commands"), list) else []:
        if isinstance(item, str):
            entries.append({"id": item, "label": item, "triggers": [item]})
        elif isinstance(item, dict):
            trigger_values = item.get("triggers") if isinstance(item.get("triggers"), list) else []
            triggers = [
                str(value).strip()
                for value in [item.get("trigger"), item.get("id"), item.get("label"), *trigger_values]
                if str(value or "").strip()
            ]
            entries.append({**item, "triggers": triggers})
    return entries


def _matches(command: dict[str, Any], normalized_text: str) -> bool:
    for trigger in command.get("triggers", []):
        normalized_trigger = _normalize(trigger)
        if normalized_trigger and normalized_text in {normalized_trigger, f"run {normalized_trigger}", f"plugin {normalized_trigger}"}:
            return True
    return False


def _execute_command(plugin: dict[str, Any], command: dict[str, Any]) -> str:
    plugin_name = str(plugin.get("name") or plugin.get("id") or "Local plugin")
    label = str(command.get("label") or command.get("id") or "plugin command")
    action = command.get("action") if isinstance(command.get("action"), dict) else {}

    if not action:
        response = command.get("response") or command.get("text")
        if response:
            return str(response)
        return (
            f"Plugin command matched: {plugin_name} / {label}. "
            "Add an action object to the plugin manifest to execute it."
        )

    return guard_action(
        "automation.run",
        f"run plugin command {plugin_name}: {label}",
        lambda: _run_action(action, plugin_name, label),
    )


def _run_action(action: dict[str, Any], plugin_name: str, label: str) -> str:
    action_type = str(action.get("type") or "response").strip().lower()

    if action_type == "response":
        return str(action.get("text") or action.get("message") or f"{plugin_name}: {label} complete.")

    if action_type == "system":
        result = launch_from_command(str(action.get("text") or action.get("command") or ""))
        return result or f"{plugin_name}: no system action matched for {label}."

    if action_type == "browser":
        result = run_browser_command(str(action.get("text") or action.get("command") or ""))
        return result or f"{plugin_name}: no browser action matched for {label}."

    if action_type == "terminal":
        return run_terminal_command(str(action.get("command") or action.get("text") or ""))

    if action_type == "sequence":
        steps = action.get("steps") if isinstance(action.get("steps"), list) else []
        results = []
        for index, step in enumerate(steps, start=1):
            if isinstance(step, str):
                step_result = launch_from_command(step) or run_browser_command(step)
            elif isinstance(step, dict):
                step_result = _run_action(step, plugin_name, f"{label} step {index}")
            else:
                step_result = None
            results.append(step_result or f"Step {index} did not match an executable action.")
        return "\n".join(results) if results else f"{plugin_name}: sequence has no steps."

    return f"{plugin_name}: unsupported plugin action type {json.dumps(action_type)}."


def _normalize(value: object) -> str:
    return " ".join(str(value or "").lower().replace("_", " ").replace("-", " ").split())

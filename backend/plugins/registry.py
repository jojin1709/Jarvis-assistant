import json
from datetime import datetime
from pathlib import Path


PLUGIN_DIR = Path(__file__).resolve().parent / "installed"
PLUGIN_DIR.mkdir(parents=True, exist_ok=True)

BUILTIN_PLUGINS = (
    {
        "id": "browser-operator",
        "name": "Visual Browser Operator",
        "description": "Runs real Playwright browser automation commands.",
        "enabled": True,
        "commands": ["search_google", "open_website", "summarize_page"],
        "source": "builtin",
    },
    {
        "id": "desktop-control",
        "name": "Desktop Control",
        "description": "Launches verified desktop apps and safe system actions.",
        "enabled": True,
        "commands": ["open_app", "close_app", "system_status"],
        "source": "builtin",
    },
    {
        "id": "coding-agent",
        "name": "Coding Agent",
        "description": "Analyzes and creates local code projects in allowed workspaces.",
        "enabled": True,
        "commands": ["analyze_project", "create_website"],
        "source": "builtin",
    },
)


def list_plugins() -> list[dict]:
    plugins = [dict(plugin) for plugin in BUILTIN_PLUGINS]
    for path in sorted(PLUGIN_DIR.glob("*.json")):
        try:
            plugin = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        plugin.setdefault("source", "local")
        plugin.setdefault("enabled", True)
        plugins.append(plugin)
    return plugins


def install_local_plugin(manifest: dict) -> dict:
    plugin_id = _clean_id(str(manifest.get("id") or manifest.get("name") or "local-plugin"))
    payload = {
        "id": plugin_id,
        "name": str(manifest.get("name") or plugin_id).strip(),
        "description": str(manifest.get("description") or "Local Jarvis plugin.").strip(),
        "enabled": bool(manifest.get("enabled", True)),
        "commands": manifest.get("commands") if isinstance(manifest.get("commands"), list) else [],
        "source": "local",
        "installedAt": datetime.now().isoformat(timespec="seconds"),
    }
    path = PLUGIN_DIR / f"{plugin_id}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def set_plugin_enabled(plugin_id: str, enabled: bool) -> dict | None:
    cleaned = _clean_id(plugin_id)
    path = PLUGIN_DIR / f"{cleaned}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    data["enabled"] = bool(enabled)
    data["updatedAt"] = datetime.now().isoformat(timespec="seconds")
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def _clean_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in value.lower().strip())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "local-plugin"

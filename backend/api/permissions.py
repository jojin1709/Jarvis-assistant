import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from api.approvals import request_approval


RUNTIME_DIR = Path(__file__).resolve().parents[1] / "runtime"
PERMISSIONS_PATH = RUNTIME_DIR / "permissions.json"
ACTIVITY_PATH = RUNTIME_DIR / "permission_activity.json"
HOME = Path.home()
PERMISSIONS_SCHEMA_VERSION = 5

DEFAULT_ALLOWED_APPS = [
    "Chrome",
    "Edge",
    "VS Code",
    "Notepad",
    "Calculator",
    "File Explorer",
    "Windows Terminal",
    "Command Prompt",
    "PowerShell",
    "Paint",
    "Spotify",
    "Discord",
]


DEFAULT_PERMISSIONS = {
    "schemaVersion": PERMISSIONS_SCHEMA_VERSION,
    "fullSystemAccess": False,
    "safeMode": False,
    "autoExecutionMode": True,
    "memoryEnabled": True,
    "controls": {
        "fileSystemAccess": True,
        "browserControl": True,
        "terminalExecution": True,
        "appControl": True,
        "voiceActivation": True,
        "automationMode": True,
        "internetAccess": True,
        "backgroundListening": True,
    },
    "confirmations": {
        "low": False,
        "medium": False,
        "high": True,
    },
    "protectedFolders": [
        str(HOME / "Documents"),
        str(HOME / "Documents" / "Passwords"),
        str(HOME / "Documents" / "Banking Files"),
        str(HOME / "Pictures"),
    ],
    "protectedFiles": [],
    "protectedApps": [
        "1password",
        "bitwarden",
        "lastpass",
        "keeper",
        "windows security",
        "banking",
    ],
    "allowedApps": DEFAULT_ALLOWED_APPS,
    "customApps": [],
    "allowedWorkspaces": [
        str(HOME / "Desktop" / "JX-JARVIS-Code"),
        str(HOME / "Desktop" / "Jarvis Workspace"),
        str(RUNTIME_DIR / "uploads"),
    ],
}


ACTION_RULES = {
    "app.open": ("appControl", "low"),
    "app.close": ("appControl", "high"),
    "app.system": ("appControl", "high"),
    "browser.open": ("browserControl", "low"),
    "browser.automation": ("browserControl", "medium"),
    "browser.sensitive": ("browserControl", "high"),
    "internet.search": ("internetAccess", "low"),
    "file.read": ("fileSystemAccess", "low"),
    "file.create": ("fileSystemAccess", "medium"),
    "file.edit": ("fileSystemAccess", "medium"),
    "file.delete": ("fileSystemAccess", "high"),
    "terminal.run": ("terminalExecution", "high"),
    "terminal.safe": ("terminalExecution", "medium"),
    "automation.run": ("automationMode", "medium"),
    "code.generate": ("fileSystemAccess", "medium"),
    "voice.listen": ("voiceActivation", "low"),
    "voice.background": ("backgroundListening", "low"),
    "memory.read": ("memoryEnabled", "low"),
    "memory.write": ("memoryEnabled", "medium"),
    "memory.clear": ("memoryEnabled", "high"),
}


@dataclass
class PermissionDecision:
    allowed: bool
    requires_confirmation: bool
    message: str
    risk: str = "low"


def permissions_state() -> dict:
    data = _load_json(PERMISSIONS_PATH, DEFAULT_PERMISSIONS)
    state = _merge_defaults(data)
    upgraded = _upgrade_permissions(state)
    if upgraded != data:
        _save_json(PERMISSIONS_PATH, upgraded)
    return upgraded


def update_permissions(patch: dict) -> dict:
    state = permissions_state()
    merged = _deep_merge(state, patch)
    merged = _merge_defaults(merged)
    _save_json(PERMISSIONS_PATH, merged)
    log_activity("Permission settings updated.", "success", "security")
    return merged


def permission_activity() -> list[dict[str, str]]:
    data = _load_json(ACTIVITY_PATH, [])
    return list(reversed(data[-160:])) if isinstance(data, list) else []


def log_activity(message: str, level: str = "info", category: str = "security") -> dict[str, str]:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    data = _load_json(ACTIVITY_PATH, [])
    if not isinstance(data, list):
        data = []
    entry = {
        "id": f"sec-{len(data) + 1}",
        "createdAt": datetime.now().isoformat(timespec="seconds"),
        "level": level,
        "category": category,
        "message": message,
    }
    data.append(entry)
    _save_json(ACTIVITY_PATH, data[-240:])
    return entry


def evaluate_permission(
    action: str,
    label: str,
    path: str | Path | None = None,
    app: str | None = None,
    command: str | None = None,
) -> PermissionDecision:
    state = permissions_state()
    control, risk = ACTION_RULES.get(action, ("automationMode", "medium"))

    if control == "memoryEnabled" and not state.get("memoryEnabled", True):
        return _deny("Memory is disabled in Security & Permissions.", risk, label)

    controls = state.get("controls", {})
    if not state.get("fullSystemAccess") and control != "memoryEnabled" and not controls.get(control, False):
        return _deny(f"Blocked by permission: {control} is disabled.", risk, label)

    if app and _is_protected_app(app, state):
        return _deny(f"Blocked: {app} is protected.", risk, label)

    if app and action in {"app.open", "app.close"} and not _is_allowed_app(app, state):
        return _deny(f"Blocked: {app} is not enabled in Apps.", risk, label)

    if path:
        path_decision = _evaluate_path(Path(path), action, state)
        if not path_decision.allowed:
            return path_decision

    needs_confirmation = bool(state.get("safeMode"))
    if not state.get("autoExecutionMode", True):
        needs_confirmation = True
    if state.get("confirmations", {}).get(risk, False):
        needs_confirmation = True

    return PermissionDecision(True, needs_confirmation, f"Allowed: {label}", risk)


def guard_action(
    action: str,
    label: str,
    callback: Callable[[], str],
    path: str | Path | None = None,
    app: str | None = None,
    command: str | None = None,
) -> str:
    decision = evaluate_permission(action, label, path=path, app=app, command=command)
    if not decision.allowed:
        log_activity(f"Denied {label}: {decision.message}", "error", "security")
        return decision.message

    if decision.requires_confirmation:
        log_activity(f"Approval requested: {label}", "warning", "security")
        return request_approval(label, lambda: _run_approved(label, callback))

    result = callback()
    log_activity(result, "success" if not _looks_failed(result) else "error", "action")
    return result


def accessible_roots(roots: list[Path]) -> list[Path]:
    state = permissions_state()
    if not state.get("controls", {}).get("fileSystemAccess", False) and not state.get("fullSystemAccess"):
        return []
    return [root for root in roots if not _path_is_protected(root, state)]


def memory_enabled() -> bool:
    return bool(permissions_state().get("memoryEnabled", True))


def _run_approved(label: str, callback: Callable[[], str]) -> str:
    result = callback()
    log_activity(result, "success" if not _looks_failed(result) else "error", "action")
    return result


def _evaluate_path(path: Path, action: str, state: dict) -> PermissionDecision:
    if _path_is_protected(path, state):
        return _deny(f"Blocked: protected path {path}.", ACTION_RULES.get(action, ("", "medium"))[1], str(path))

    if action in {"file.create", "file.edit", "file.delete", "code.generate"} and not state.get("fullSystemAccess"):
        if not _path_in_any(path, state.get("allowedWorkspaces", [])):
            return _deny(
                f"Blocked: {path} is outside allowed workspaces.",
                ACTION_RULES.get(action, ("", "medium"))[1],
                str(path),
            )

    return PermissionDecision(True, False, "Path allowed.")


def _path_is_protected(path: Path, state: dict) -> bool:
    return _path_in_any(path, state.get("protectedFolders", [])) or _same_as_any(path, state.get("protectedFiles", []))


def _path_in_any(path: Path, roots: list[str]) -> bool:
    candidate = _resolve(path)
    for root in roots:
        resolved_root = _resolve(Path(str(root)).expanduser())
        try:
            candidate.relative_to(resolved_root)
            return True
        except ValueError:
            continue
    return False


def _same_as_any(path: Path, values: list[str]) -> bool:
    candidate = _resolve(path)
    return any(candidate == _resolve(Path(str(value)).expanduser()) for value in values)


def _resolve(path: Path) -> Path:
    try:
        return path.expanduser().resolve()
    except OSError:
        return path.expanduser().absolute()


def _is_protected_app(app: str, state: dict) -> bool:
    normalized = app.lower().strip()
    return any(item.lower().strip() in normalized or normalized in item.lower().strip() for item in state.get("protectedApps", []))


def _is_allowed_app(app: str, state: dict) -> bool:
    allowed = state.get("allowedApps", [])
    normalized = _normalize_app_name(app)
    for item in allowed:
        allowed_name = _normalize_app_name(item)
        if not allowed_name:
            continue
        if allowed_name == normalized:
            return True
        if len(allowed_name) >= 4 and allowed_name in normalized:
            return True
        if len(normalized) >= 4 and normalized in allowed_name:
            return True
    return False


def app_is_allowed(app: str) -> bool:
    return _is_allowed_app(app, permissions_state())


def _normalize_app_name(value: object) -> str:
    return " ".join(str(value or "").lower().replace("-", " ").replace("_", " ").split())


def _deny(message: str, risk: str, label: str, confirmable: bool = False) -> PermissionDecision:
    return PermissionDecision(False, confirmable, message, risk)


def _looks_failed(result: str) -> bool:
    lowered = result.lower()
    return any(phrase in lowered for phrase in ("blocked", "denied", "could not", "failed", "not found", "error"))


def _load_json(path: Path, fallback):
    if not path.exists():
        return deepcopy(fallback)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return deepcopy(fallback)


def _save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _merge_defaults(data: dict) -> dict:
    merged = _deep_merge(deepcopy(DEFAULT_PERMISSIONS), data if isinstance(data, dict) else {})
    for key in ("allowedWorkspaces", "protectedApps"):
        merged[key] = _dedupe([*DEFAULT_PERMISSIONS.get(key, []), *merged.get(key, [])])
    merged["allowedApps"] = _dedupe(merged.get("allowedApps", []))
    merged["customApps"] = _dedupe_custom_apps(merged.get("customApps", []))
    return merged


def _upgrade_permissions(state: dict) -> dict:
    version = int(state.get("schemaVersion") or 0)
    if version < 2:
        controls = state.setdefault("controls", {})
        controls["automationMode"] = True
        confirmations = state.setdefault("confirmations", {})
        confirmations["medium"] = False
    if version < 3:
        state["allowedApps"] = _dedupe([*DEFAULT_ALLOWED_APPS, *state.get("allowedApps", [])])
    if version < 4:
        state["customApps"] = _dedupe_custom_apps(state.get("customApps", []))
    if version < 5:
        state.setdefault("controls", {})["terminalExecution"] = True
    state["schemaVersion"] = PERMISSIONS_SCHEMA_VERSION
    return state


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        normalized = str(value).strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(str(value))
    return result


def _dedupe_custom_apps(values: list[dict]) -> list[dict[str, str]]:
    seen = set()
    result = []
    for value in values if isinstance(values, list) else []:
        if not isinstance(value, dict):
            continue
        label = str(value.get("label") or "").strip()
        path = str(value.get("path") or "").strip()
        if not label or not path:
            continue
        key = f"{label.lower()}::{path.lower()}"
        if key in seen:
            continue
        seen.add(key)
        result.append(
            {
                "label": label,
                "path": path,
                "kind": str(value.get("kind") or "exe"),
                "source": str(value.get("source") or "custom"),
            }
        )
    return result


def _deep_merge(base: dict, patch: dict) -> dict:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_merge(base[key], value)
        else:
            base[key] = value
    return base

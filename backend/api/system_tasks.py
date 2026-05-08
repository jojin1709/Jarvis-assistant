import os
import platform
import random
import re
import shutil
import subprocess
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

from api.approvals import request_approval
from api.permissions import accessible_roots, evaluate_permission, guard_action
from app.config import settings
from api.code_writer import open_code_workspace, open_latest_code_project, test_latest_code_project


DESKTOP = Path.home() / "Desktop"
DOCUMENTS = Path.home() / "Documents"
DOWNLOADS = Path.home() / "Downloads"
MUSIC = Path.home() / "Music"
PICTURES = Path.home() / "Pictures"
VIDEOS = Path.home() / "Videos"
SAFE_FILE_ROOTS = [DESKTOP, DOCUMENTS, DOWNLOADS, PICTURES, VIDEOS, MUSIC]
JARVIS_TRASH = DESKTOP / "JX-JARVIS-Trash"
LOCAL_APP_DATA = Path(os.getenv("LOCALAPPDATA", ""))
APP_DATA = Path(os.getenv("APPDATA", ""))
PROGRAM_FILES = Path(os.getenv("ProgramFiles", ""))
PROGRAM_FILES_X86 = Path(os.getenv("ProgramFiles(x86)", ""))


APP_TARGETS = {
    "chrome": {
        "label": "Chrome",
        "commands": ["chrome.exe", "chrome"],
        "processes": ["chrome.exe"],
        "paths": [
            PROGRAM_FILES / "Google" / "Chrome" / "Application" / "chrome.exe",
            PROGRAM_FILES_X86 / "Google" / "Chrome" / "Application" / "chrome.exe",
            LOCAL_APP_DATA / "Google" / "Chrome" / "Application" / "chrome.exe",
        ],
        "fallback_url": "https://www.google.com",
    },
    "edge": {
        "label": "Edge",
        "commands": ["msedge.exe", "msedge"],
        "processes": ["msedge.exe"],
        "paths": [
            PROGRAM_FILES / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            PROGRAM_FILES_X86 / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        ],
        "fallback_url": "https://www.google.com",
    },
    "vs code": {
        "label": "VS Code",
        "commands": ["code.cmd", "code.exe", "code"],
        "processes": ["Code.exe"],
        "paths": [
            LOCAL_APP_DATA / "Programs" / "Microsoft VS Code" / "Code.exe",
            PROGRAM_FILES / "Microsoft VS Code" / "Code.exe",
        ],
    },
    "notepad": {"label": "Notepad", "commands": ["notepad.exe"], "processes": ["notepad.exe"]},
    "calculator": {"label": "Calculator", "commands": ["calc.exe"], "processes": ["CalculatorApp.exe", "calc.exe"]},
    "file explorer": {"label": "File Explorer", "commands": ["explorer.exe"], "processes": ["explorer.exe"]},
    "terminal": {"label": "Windows Terminal", "commands": ["wt.exe"], "processes": ["WindowsTerminal.exe", "wt.exe"]},
    "command prompt": {"label": "Command Prompt", "commands": ["cmd.exe"], "processes": ["cmd.exe"]},
    "powershell": {"label": "PowerShell", "commands": ["powershell.exe"], "processes": ["powershell.exe"]},
    "task manager": {"label": "Task Manager", "commands": ["taskmgr.exe"], "processes": ["Taskmgr.exe"]},
    "paint": {"label": "Paint", "commands": ["mspaint.exe"], "processes": ["mspaint.exe"]},
    "spotify": {
        "label": "Spotify",
        "commands": ["spotify.exe"],
        "processes": ["Spotify.exe"],
        "paths": [APP_DATA / "Spotify" / "Spotify.exe"],
        "fallback_url": "https://open.spotify.com",
    },
    "discord": {
        "label": "Discord",
        "commands": ["Discord.exe"],
        "processes": ["Discord.exe"],
        "path_globs": [LOCAL_APP_DATA / "Discord" / "app-*" / "Discord.exe"],
        "fallback_url": "https://discord.com/app",
    },
}

APP_ALIASES = {
    "google chrome": "chrome",
    "microsoft edge": "edge",
    "explorer": "file explorer",
    "windows explorer": "file explorer",
    "files": "file explorer",
    "visual studio code": "vs code",
    "vscode": "vs code",
    "windows terminal": "terminal",
    "cmd": "command prompt",
    "power shell": "powershell",
    "taskmanager": "task manager",
    "ms paint": "paint",
}


def _run_detached(command: list[str]) -> subprocess.Popen:
    return subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
    )


def _process_snapshot() -> set[str]:
    if os.name != "nt":
        return set()
    try:
        output = subprocess.check_output(
            ["tasklist", "/fo", "csv", "/nh"],
            text=True,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    return {line.split('","', 1)[0].strip('"').lower() for line in output.splitlines() if line.strip()}


def _process_running(process_names: list[str]) -> bool:
    if not process_names:
        return True
    if os.name != "nt":
        return True
    processes = _process_snapshot()
    wanted = {name.lower() for name in process_names}
    return bool(processes.intersection(wanted))


def _wait_for_process(process_names: list[str], timeout: float = 4.0, expect_running: bool = True) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        running = _process_running(process_names)
        if running == expect_running:
            return True
        time.sleep(0.25)
    return _process_running(process_names) == expect_running


def _launch_and_verify(command: list[str], label: str, process_names: list[str] | None = None) -> str:
    try:
        process = _run_detached(command)
    except OSError as error:
        return f"Could not open {label}: {error}"

    if process_names and not _wait_for_process(process_names):
        return f"{label} launch was attempted, but the process was not detected."
    if not process_names and process.poll() not in (None, 0):
        return f"{label} launch failed with exit code {process.poll()}."
    return f"{label} opened successfully."


def system_status() -> str:
    return (
        f"System online. OS: {platform.system()} {platform.release()}. "
        f"Machine: {platform.node()}. Processor: {platform.processor() or 'available'}."
    )


def list_desktop() -> str:
    def run() -> str:
        if not DESKTOP.exists():
            return "Desktop folder was not found."
        items = sorted(path.name for path in DESKTOP.iterdir())[:18]
        if not items:
            return "Desktop is currently empty."
        return "Desktop scan complete. Items found: " + ", ".join(items)

    return guard_action("file.read", "scan desktop", run, path=DESKTOP)


def current_time() -> str:
    return "The current time is " + datetime.now().strftime("%I:%M %p")


def current_date() -> str:
    return "Today is " + datetime.now().strftime("%A, %B %d, %Y")


def create_desktop_note() -> str:
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = DESKTOP / f"JX-JARVIS-note-{stamp}.txt"

    def run() -> str:
        DESKTOP.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "JX JARVIS mission note\n"
            f"Created: {datetime.now().isoformat(timespec='seconds')}\n\n"
            "Add your task details here.\n",
            encoding="utf-8",
        )
        return f"Created desktop note: {path.name}"

    return guard_action("file.create", f"create desktop note {path.name}", run, path=path)


def open_folder(path: Path, label: str) -> str:
    if not path.exists():
        return f"{label} folder was not found."
    return guard_action(
        "file.read",
        f"open {label} folder",
        lambda: _launch_and_verify(["explorer.exe", str(path)], f"{label} folder", ["explorer.exe"]),
        path=path,
    )


def open_website(url: str, label: str) -> str:
    def run() -> str:
        opened = webbrowser.open(url)
        return f"{label} opened in the browser." if opened else f"Could not open {label} in the browser."

    return guard_action("browser.open", f"open {label}", run)


def open_protocol(protocol: str, label: str) -> str:
    return guard_action(
        "app.open",
        f"open {label}",
        lambda: _launch_and_verify(["explorer.exe", protocol], label, ["explorer.exe"]),
        app=label,
    )


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _first_glob(patterns: list[Path]) -> Path | None:
    for pattern in patterns:
        parent = pattern.parent
        if not parent.parent.exists():
            continue
        matches = sorted(parent.parent.glob(f"{parent.name}/{pattern.name}"), reverse=True)
        for match in matches:
            if match.exists():
                return match
    return None


def _app_config(target: str) -> dict | None:
    normalized = " ".join(target.lower().strip().split())
    normalized = normalized.removeprefix("the ").strip()
    key = APP_ALIASES.get(normalized, normalized)
    return APP_TARGETS.get(key)


def _resolve_app_command(config: dict) -> list[str] | None:
    for command in config.get("commands", []):
        resolved = shutil.which(command)
        if resolved:
            return [resolved]

    found = _first_existing(config.get("paths", []))
    if found:
        return [str(found)]

    globbed = _first_glob(config.get("path_globs", []))
    if globbed:
        return [str(globbed)]

    return None


def open_app_target(target: str) -> str | None:
    config = _app_config(target)
    if not config:
        return None

    command = _resolve_app_command(config)
    label = config["label"]
    if command:
        return guard_action(
            "app.open",
            f"open {label}",
            lambda: _launch_and_verify(command, label, config.get("processes")),
            app=label,
        )

    fallback_url = config.get("fallback_url")
    if fallback_url:
        return open_website(fallback_url, label)

    return f"{label} was not found on this PC."


def close_app_target(target: str) -> str | None:
    config = _app_config(target)
    if not config:
        return None

    label = config["label"]
    processes = config.get("processes", [])
    if not processes:
        return f"{label} does not have a safe close mapping yet."
    def run() -> str:
        if not _process_running(processes):
            return f"{label} is not running."

        for process_name in processes:
            subprocess.run(
                ["taskkill", "/im", process_name, "/t", "/f"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                check=False,
            )

        if _wait_for_process(processes, timeout=4.0, expect_running=False):
            return f"{label} closed successfully."
        return f"Tried to close {label}, but it still appears to be running."

    return guard_action("app.close", f"close {label}", run, app=label)


def list_available_apps() -> list[dict[str, object]]:
    apps = []
    for key, config in APP_TARGETS.items():
        command = _resolve_app_command(config)
        processes = config.get("processes", [])
        apps.append(
            {
                "id": key,
                "label": config["label"],
                "installed": bool(command),
                "running": _process_running(processes),
                "fallback_url": config.get("fallback_url"),
            }
        )
    return apps


def _open_app(exe_names: list[str], fallback_url: str | None, label: str) -> str:
    for exe in exe_names:
        resolved = shutil.which(exe)
        if resolved:
            return _launch_and_verify([resolved], label, [Path(exe).name])

    local_app_data = os.getenv("LOCALAPPDATA", "")
    program_files = os.getenv("ProgramFiles", "")
    program_files_x86 = os.getenv("ProgramFiles(x86)", "")
    if label.lower() == "chrome":
        known_paths = [
            Path(program_files) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(program_files_x86) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(local_app_data) / "Google" / "Chrome" / "Application" / "chrome.exe",
        ]
    else:
        known_paths = [
            Path(program_files) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            Path(program_files_x86) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        ]
    found = _first_existing(known_paths)
    if found:
        return _launch_and_verify([str(found)], label, [found.name])

    if fallback_url:
        return open_website(fallback_url, label)

    return f"{label} was not found."


def _open_program(exe_names: list[str], label: str, fallback_url: str | None = None) -> str:
    for exe in exe_names:
        resolved = shutil.which(exe)
        if resolved:
            return _launch_and_verify([resolved], label, [Path(exe).name])

    if fallback_url:
        return open_website(fallback_url, label)

    return f"{label} was not found."


def open_chrome() -> str:
    return open_app_target("chrome") or "Chrome was not found."


def open_edge() -> str:
    return open_app_target("edge") or "Edge was not found."


def open_screen_snip() -> str:
    return guard_action(
        "app.open",
        "open screenshot snip",
        lambda: _launch_and_verify(["explorer.exe", "ms-screenclip:"], "Screenshot snip", ["explorer.exe"]),
        app="Screenshot snip",
    )


def _power_action(action: str) -> str:
    commands = {
        "shutdown": ["shutdown", "/s", "/t", "15"],
        "restart": ["shutdown", "/r", "/t", "15"],
        "lock": ["rundll32.exe", "user32.dll,LockWorkStation"],
    }
    command = commands.get(action)
    if not command:
        return "Unsupported power action."

    def run() -> str:
        try:
            _run_detached(command)
        except OSError as error:
            return f"Could not {action} this PC: {error}"
        return f"{action.capitalize()} command started."

    return guard_action("app.system", f"{action} this PC", run)


def search_youtube(query: str) -> str:
    def run() -> str:
        webbrowser.open(f"https://www.youtube.com/results?search_query={quote_plus(query)}")
        return f"Searching YouTube for {query}."

    return guard_action("internet.search", f"search YouTube for {query}", run)


WEBSITE_TARGETS = {
    "amazon": ("https://www.amazon.in", "Amazon"),
    "amazon india": ("https://www.amazon.in", "Amazon"),
    "chatgpt": ("https://chatgpt.com", "ChatGPT"),
    "discord": ("https://discord.com/app", "Discord"),
    "facebook": ("https://www.facebook.com", "Facebook"),
    "flipkart": ("https://www.flipkart.com", "Flipkart"),
    "google drive": ("https://drive.google.com", "Google Drive"),
    "google docs": ("https://docs.google.com", "Google Docs"),
    "gmail": ("https://mail.google.com", "Gmail"),
    "github": ("https://github.com", "GitHub"),
    "instagram": ("https://www.instagram.com", "Instagram"),
    "linkedin": ("https://www.linkedin.com", "LinkedIn"),
    "netflix": ("https://www.netflix.com", "Netflix"),
    "sarvam": ("https://dashboard.sarvam.ai", "Sarvam dashboard"),
    "sarvam dashboard": ("https://dashboard.sarvam.ai", "Sarvam dashboard"),
    "sarvam ai": ("https://dashboard.sarvam.ai", "Sarvam dashboard"),
    "whatsapp": ("https://web.whatsapp.com", "WhatsApp"),
    "x": ("https://x.com", "X"),
    "twitter": ("https://x.com", "X"),
    "youtube": ("https://www.youtube.com", "YouTube"),
}


def _open_common_target(target: str) -> str | None:
    normalized = " ".join(target.lower().strip().split())
    normalized = normalized.removeprefix("the ").strip()
    normalized = normalized.replace("visual studio code", "vs code")

    app_response = open_app_target(normalized)
    if app_response:
        return app_response

    if normalized in WEBSITE_TARGETS:
        url, label = WEBSITE_TARGETS[normalized]
        return open_website(url, label)

    if normalized in {"settings", "windows settings"}:
        return open_protocol("ms-settings:", "Settings")
    if normalized in {"camera", "windows camera"}:
        return open_protocol("microsoft.windows.camera:", "Camera")

    if re.fullmatch(r"(https?://)?[a-z0-9-]+(\.[a-z0-9-]+)+(/[^\s]*)?", normalized):
        url = normalized if normalized.startswith(("http://", "https://")) else f"https://{normalized}"
        return open_website(url, normalized)

    return None


def run_open_target_action(text: str) -> str | None:
    open_match = re.search(r"\b(?:open|launch|start)\s+(.+)$", text, re.IGNORECASE)
    if not open_match:
        return None

    target = open_match.group(1).strip(" .")
    if re.match(r"^(?:file|folder)\b", target, re.IGNORECASE):
        return None
    if " latest code" in f" {target.lower()}":
        return None

    return _open_common_target(target)


def run_close_target_action(text: str) -> str | None:
    close_match = re.search(r"\b(?:close|quit|exit|stop)\s+(.+)$", text, re.IGNORECASE)
    if not close_match:
        return None

    target = close_match.group(1).strip(" .")
    if target.lower() in {"app", "application", "program", "window"}:
        return None
    return close_app_target(target)


def play_music() -> str:
    def run() -> str:
        if not MUSIC.exists():
            return "Music folder was not found."

        songs = [
            path
            for path in MUSIC.iterdir()
            if path.is_file() and path.suffix.lower() in {".mp3", ".wav", ".m4a", ".flac", ".aac", ".wma"}
        ]
        if not songs:
            return "No playable music files were found in your Music folder."

        song = random.choice(songs)
        os.startfile(song)
        return f"Playing {song.name}."

    return guard_action("file.read", "play music from Music folder", run, path=MUSIC)


TASKS = {
    "system_status": system_status,
    "list_desktop": list_desktop,
    "create_note": create_desktop_note,
    "open_notepad": lambda: open_app_target("notepad") or "Notepad was not found.",
    "open_calculator": lambda: open_app_target("calculator") or "Calculator was not found.",
    "open_explorer": lambda: open_folder(Path.home(), "File Explorer"),
    "open_desktop": lambda: open_folder(DESKTOP, "Desktop"),
    "open_documents": lambda: open_folder(DOCUMENTS, "Documents"),
    "open_downloads": lambda: open_folder(DOWNLOADS, "Downloads"),
    "open_pictures": lambda: open_folder(PICTURES, "Pictures"),
    "open_videos": lambda: open_folder(VIDEOS, "Videos"),
    "open_youtube": lambda: open_website("https://www.youtube.com", "YouTube"),
    "open_google": lambda: open_website("https://www.google.com", "Google"),
    "open_gmail": lambda: open_website("https://mail.google.com", "Gmail"),
    "open_github": lambda: open_website("https://github.com", "GitHub"),
    "open_whatsapp": lambda: open_website("https://web.whatsapp.com", "WhatsApp"),
    "open_chrome": open_chrome,
    "open_edge": open_edge,
    "take_screenshot": open_screen_snip,
    "shutdown_pc": lambda: _power_action("shutdown"),
    "restart_pc": lambda: _power_action("restart"),
    "lock_pc": lambda: _power_action("lock"),
    "play_music": play_music,
    "open_vscode": open_code_workspace,
    "open_latest_code": open_latest_code_project,
    "test_latest_code": test_latest_code_project,
    "current_time": current_time,
    "current_date": current_date,
}


COMMAND_ALIASES = {
    "open notepad": "open_notepad",
    "launch notepad": "open_notepad",
    "open calculator": "open_calculator",
    "launch calculator": "open_calculator",
    "open explorer": "open_explorer",
    "open file explorer": "open_explorer",
    "show desktop": "list_desktop",
    "list desktop": "list_desktop",
    "scan desktop": "list_desktop",
    "system status": "system_status",
    "status report": "system_status",
    "create note": "create_note",
    "make note": "create_note",
    "open youtube": "open_youtube",
    "launch youtube": "open_youtube",
    "open google": "open_google",
    "launch google": "open_google",
    "open gmail": "open_gmail",
    "launch gmail": "open_gmail",
    "open github": "open_github",
    "launch github": "open_github",
    "open whatsapp": "open_whatsapp",
    "open web whatsapp": "open_whatsapp",
    "launch whatsapp": "open_whatsapp",
    "open chrome": "open_chrome",
    "launch chrome": "open_chrome",
    "open edge": "open_edge",
    "launch edge": "open_edge",
    "take screenshot": "take_screenshot",
    "capture screenshot": "take_screenshot",
    "screenshot": "take_screenshot",
    "open vscode": "open_vscode",
    "open vs code": "open_vscode",
    "open visual studio code": "open_vscode",
    "launch vscode": "open_vscode",
    "launch vs code": "open_vscode",
    "open latest code": "open_latest_code",
    "open last code": "open_latest_code",
    "open latest project": "open_latest_code",
    "test latest code": "test_latest_code",
    "test last code": "test_latest_code",
    "run latest code": "test_latest_code",
    "run last code": "test_latest_code",
    "play music": "play_music",
    "open music": "play_music",
    "what time": "current_time",
    "current time": "current_time",
    "tell me time": "current_time",
    "what date": "current_date",
    "current date": "current_date",
    "today date": "current_date",
    "open desktop": "open_desktop",
    "open documents": "open_documents",
    "open downloads": "open_downloads",
    "open pictures": "open_pictures",
    "open videos": "open_videos",
    "shutdown pc": "shutdown_pc",
    "shut down pc": "shutdown_pc",
    "shutdown computer": "shutdown_pc",
    "restart pc": "restart_pc",
    "restart computer": "restart_pc",
    "lock pc": "lock_pc",
    "lock computer": "lock_pc",
}


def _root_by_name(name: str) -> Path | None:
    normalized = name.lower().strip()
    roots = {
        "desktop": DESKTOP,
        "document": DOCUMENTS,
        "documents": DOCUMENTS,
        "download": DOWNLOADS,
        "downloads": DOWNLOADS,
        "picture": PICTURES,
        "pictures": PICTURES,
        "video": VIDEOS,
        "videos": VIDEOS,
        "music": MUSIC,
    }
    return roots.get(normalized)


def _safe_file_name(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1F]+', "-", name).strip(" .-")
    return cleaned[:80] or "jarvis-item"


def _find_matching_paths(query: str, limit: int = 8) -> list[Path]:
    lowered = query.lower().strip()
    if not lowered:
        return []

    matches: list[Path] = []
    scanned = 0
    for root in accessible_roots(SAFE_FILE_ROOTS):
        if not root.exists():
            continue
        for path in root.rglob("*"):
            scanned += 1
            if scanned > 12000 or len(matches) >= limit:
                break
            if lowered in path.name.lower():
                matches.append(path)
        if scanned > 12000 or len(matches) >= limit:
            break
    return matches


def _format_matches(matches: list[Path]) -> str:
    return "\n".join(str(path) for path in matches)


def _permission_error(*decisions) -> str | None:
    for decision in decisions:
        if not decision.allowed:
            return decision.message
    return None


def _open_path_match(query: str) -> str:
    matches = _find_matching_paths(query, limit=3)
    if not matches:
        return f"No file or folder found for '{query}'."

    return guard_action("file.read", f"open {matches[0]}", lambda: (os.startfile(matches[0]) or f"Opened: {matches[0]}"), path=matches[0])


def _create_folder(name: str, root: Path) -> str:
    target = root / _safe_file_name(name)

    def run() -> str:
        try:
            root.mkdir(parents=True, exist_ok=True)
            target.mkdir(exist_ok=True)
        except OSError as error:
            return f"Could not create folder: {error}"
        return f"Folder ready: {target}"

    return guard_action("file.create", f"create folder {target}", run, path=target)


def _move_first_match(query: str, destination: Path) -> str:
    matches = _find_matching_paths(query, limit=1)
    if not matches:
        return f"No file or folder found for '{query}'."

    source = matches[0]
    target_decision = evaluate_permission("file.create", f"move to {destination}", path=destination)
    source_decision = evaluate_permission("file.delete", f"move {source}", path=source)
    denied = _permission_error(target_decision, source_decision)
    if denied:
        return denied

    destination.mkdir(parents=True, exist_ok=True)
    target = destination / source.name
    if target.exists():
        target = destination / f"{source.stem}-{datetime.now().strftime('%Y%m%d-%H%M%S')}{source.suffix}"
    try:
        shutil.move(str(source), str(target))
    except OSError as error:
        return f"Could not move {source.name}: {error}"
    return f"Moved {source.name} to {target}."


def _rename_first_match(query: str, new_name: str) -> str:
    matches = _find_matching_paths(query, limit=1)
    if not matches:
        return f"No file or folder found for '{query}'."

    source = matches[0]
    clean_name = _safe_file_name(new_name)
    if source.is_file() and "." not in Path(clean_name).name and source.suffix:
        clean_name += source.suffix
    target = source.with_name(clean_name)
    denied = _permission_error(
        evaluate_permission("file.edit", f"rename {source}", path=source),
        evaluate_permission("file.create", f"rename to {target}", path=target),
    )
    if denied:
        return denied

    if target.exists():
        return f"Cannot rename. Target already exists: {target.name}"
    try:
        source.rename(target)
    except OSError as error:
        return f"Could not rename {source.name}: {error}"
    return f"Renamed {source.name} to {target.name}."


def _trash_first_match(query: str) -> str:
    matches = _find_matching_paths(query, limit=1)
    if not matches:
        return f"No file or folder found for '{query}'."

    source = matches[0]
    denied = _permission_error(
        evaluate_permission("file.delete", f"delete {source}", path=source),
        evaluate_permission("file.create", f"move to Jarvis trash", path=JARVIS_TRASH),
    )
    if denied:
        return denied

    JARVIS_TRASH.mkdir(parents=True, exist_ok=True)
    target = JARVIS_TRASH / source.name
    if target.exists():
        target = JARVIS_TRASH / f"{source.stem}-{datetime.now().strftime('%Y%m%d-%H%M%S')}{source.suffix}"
    try:
        shutil.move(str(source), str(target))
    except OSError as error:
        return f"Could not move {source.name} to Jarvis trash: {error}"
    return f"Moved {source.name} to Jarvis trash: {target}."


def extract_youtube_search(text: str) -> str | None:
    normalized = " ".join(text.lower().strip().split())
    triggers = ["search youtube for", "youtube search", "search on youtube for"]
    for trigger in triggers:
        if trigger in normalized:
            query = normalized.split(trigger, 1)[1].strip(" :.-")
            return query or None
    return None


def run_local_file_action(text: str) -> str | None:
    normalized = " ".join(text.lower().strip().split())

    open_match = re.search(r"\bopen (?:file|folder)\s+(.+)$", text, re.IGNORECASE)
    if open_match:
        return _open_path_match(open_match.group(1).strip())

    create_match = re.search(
        r"\b(?:create|make)\s+(?:a\s+)?folder\s+(?:called\s+|named\s+)?(.+?)(?:\s+(?:on|in)\s+(desktop|documents|downloads|pictures|videos|music))?$",
        text,
        re.IGNORECASE,
    )
    if create_match:
        root = _root_by_name(create_match.group(2) or "desktop") or DESKTOP
        return _create_folder(create_match.group(1), root)

    move_match = re.search(
        r"\bmove\s+(?:file|folder)?\s*(.+?)\s+to\s+(desktop|documents|downloads|pictures|videos|music)$",
        text,
        re.IGNORECASE,
    )
    if move_match:
        query = move_match.group(1).strip()
        destination = _root_by_name(move_match.group(2)) or DESKTOP
        return request_approval(f"move '{query}' to {destination}", lambda: _move_first_match(query, destination))

    rename_match = re.search(r"\brename\s+(?:file|folder)?\s*(.+?)\s+to\s+(.+)$", text, re.IGNORECASE)
    if rename_match:
        query = rename_match.group(1).strip()
        new_name = rename_match.group(2).strip()
        return request_approval(f"rename '{query}' to '{new_name}'", lambda: _rename_first_match(query, new_name))

    delete_match = re.search(r"\b(?:delete|remove)\s+(?:file|folder)?\s*(.+)$", text, re.IGNORECASE)
    if delete_match and "memory" not in normalized:
        query = delete_match.group(1).strip()
        return request_approval(f"move '{query}' to Jarvis trash", lambda: _trash_first_match(query))

    return None


def run_system_task(task_id: str) -> str:
    if not settings.system_tasks_enabled:
        return "System task access is disabled in configuration."

    task = TASKS.get(task_id)
    if not task:
        return "That system task is not in the safe action list."

    return task()


def match_system_command(text: str) -> str | None:
    normalized = " ".join(text.lower().strip().split())
    for phrase, task_id in COMMAND_ALIASES.items():
        if phrase in normalized:
            return task_id
    return None


def extract_file_search(text: str) -> str | None:
    normalized = " ".join(text.lower().strip().split())
    triggers = ["find file", "search file", "search desktop for", "find desktop file", "find my file"]
    for trigger in triggers:
        if trigger in normalized:
            query = normalized.split(trigger, 1)[1].strip(" :.-")
            return query or None
    return None


def extract_google_search(text: str) -> str | None:
    normalized = " ".join(text.lower().strip().split())
    triggers = ["google search", "search google for", "search the web for", "search for"]
    for trigger in triggers:
        if trigger in normalized:
            query = normalized.split(trigger, 1)[1].strip(" :.-")
            return query or None
    return None


def open_google_search(query: str) -> str:
    def run() -> str:
        webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")
        return f"Searching Google for {query}."

    return guard_action("internet.search", f"search Google for {query}", run)


def search_user_files(query: str) -> str:
    if not settings.system_tasks_enabled:
        return "System task access is disabled in configuration."

    roots = accessible_roots([Path.home() / name for name in ("Desktop", "Documents", "Downloads", "Videos", "Pictures")])
    if not roots:
        return "File search is blocked by Security & Permissions."
    matches: list[Path] = []
    lowered = query.lower()
    scanned = 0

    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            scanned += 1
            if scanned > 8000 or len(matches) >= 12:
                break
            if lowered in path.name.lower():
                matches.append(path)
        if scanned > 8000 or len(matches) >= 12:
            break

    if not matches:
        return f"No matching files found for '{query}' in Desktop, Documents, Downloads, Videos, or Pictures."

    lines = [f"Found {len(matches)} matching file(s) for '{query}':"]
    lines.extend(str(path) for path in matches)
    return "\n".join(lines)

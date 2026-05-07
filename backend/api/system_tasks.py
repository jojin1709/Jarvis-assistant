import os
import platform
import random
import re
import shutil
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

from api.approvals import request_approval
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


def _run_detached(command: list[str]) -> None:
    subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
    )


def system_status() -> str:
    return (
        f"System online. OS: {platform.system()} {platform.release()}. "
        f"Machine: {platform.node()}. Processor: {platform.processor() or 'available'}."
    )


def list_desktop() -> str:
    if not DESKTOP.exists():
        return "Desktop folder was not found."
    items = sorted(path.name for path in DESKTOP.iterdir())[:18]
    if not items:
        return "Desktop is currently empty."
    return "Desktop scan complete. Items found: " + ", ".join(items)


def current_time() -> str:
    return "The current time is " + datetime.now().strftime("%I:%M %p")


def current_date() -> str:
    return "Today is " + datetime.now().strftime("%A, %B %d, %Y")


def create_desktop_note() -> str:
    DESKTOP.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = DESKTOP / f"JX-JARVIS-note-{stamp}.txt"
    path.write_text(
        "JX JARVIS mission note\n"
        f"Created: {datetime.now().isoformat(timespec='seconds')}\n\n"
        "Add your task details here.\n",
        encoding="utf-8",
    )
    return f"Created desktop note: {path.name}"


def open_folder(path: Path, label: str) -> str:
    if not path.exists():
        return f"{label} folder was not found."
    _run_detached(["explorer.exe", str(path)])
    return f"{label} folder opened."


def open_website(url: str, label: str) -> str:
    webbrowser.open(url)
    return f"{label} opened."


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _open_app(exe_names: list[str], fallback_url: str | None, label: str) -> str:
    for exe in exe_names:
        resolved = shutil.which(exe)
        if resolved:
            _run_detached([resolved])
            return f"{label} opened."

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
        _run_detached([str(found)])
        return f"{label} opened."

    if fallback_url:
        webbrowser.open(fallback_url)
        return f"{label} opened in the browser."

    return f"{label} was not found."


def open_chrome() -> str:
    return _open_app(["chrome.exe", "chrome"], "https://www.google.com", "Chrome")


def open_edge() -> str:
    return _open_app(["msedge.exe", "msedge"], "https://www.google.com", "Edge")


def open_screen_snip() -> str:
    _run_detached(["explorer.exe", "ms-screenclip:"])
    return "Screenshot snip opened."


def search_youtube(query: str) -> str:
    webbrowser.open(f"https://www.youtube.com/results?search_query={quote_plus(query)}")
    return f"Searching YouTube for {query}."


def play_music() -> str:
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


TASKS = {
    "system_status": system_status,
    "list_desktop": list_desktop,
    "create_note": create_desktop_note,
    "open_notepad": lambda: (_run_detached(["notepad.exe"]) or "Notepad opened."),
    "open_calculator": lambda: (_run_detached(["calc.exe"]) or "Calculator opened."),
    "open_explorer": lambda: (_run_detached(["explorer.exe", str(Path.home())]) or "File Explorer opened."),
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
    for root in SAFE_FILE_ROOTS:
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


def _open_path_match(query: str) -> str:
    matches = _find_matching_paths(query, limit=3)
    if not matches:
        return f"No file or folder found for '{query}'."

    os.startfile(matches[0])
    return f"Opened: {matches[0]}"


def _create_folder(name: str, root: Path) -> str:
    try:
        root.mkdir(parents=True, exist_ok=True)
        target = root / _safe_file_name(name)
        target.mkdir(exist_ok=True)
    except OSError as error:
        return f"Could not create folder: {error}"
    return f"Folder ready: {target}"


def _move_first_match(query: str, destination: Path) -> str:
    matches = _find_matching_paths(query, limit=1)
    if not matches:
        return f"No file or folder found for '{query}'."

    source = matches[0]
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
    webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")
    return f"Searching Google for {query}."


def search_user_files(query: str) -> str:
    if not settings.system_tasks_enabled:
        return "System task access is disabled in configuration."

    roots = [Path.home() / name for name in ("Desktop", "Documents", "Downloads", "Videos", "Pictures")]
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

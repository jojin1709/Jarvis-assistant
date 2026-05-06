import os
import platform
import random
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

from app.config import settings


DESKTOP = Path.home() / "Desktop"
DOCUMENTS = Path.home() / "Documents"
DOWNLOADS = Path.home() / "Downloads"
MUSIC = Path.home() / "Music"
PICTURES = Path.home() / "Pictures"
VIDEOS = Path.home() / "Videos"


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
    "play_music": play_music,
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

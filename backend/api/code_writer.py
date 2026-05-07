import json
import os
import re
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path, PurePosixPath


CODE_ROOT = Path.home() / "Desktop" / "JX-JARVIS-Code"
MAX_FILES = 8
MAX_FILE_CHARS = 30000


CODE_TRIGGERS = (
    "can you write code for",
    "can you write a code for",
    "can you write me code for",
    "can you write me the code for",
    "can you make code for",
    "can you make me code for",
    "can you make a",
    "can you make an",
    "can you build a",
    "can you build an",
    "can you create a",
    "can you create an",
    "can u write code for",
    "can u write me code for",
    "can u make a",
    "can u make an",
    "can u build a",
    "can u build an",
    "i want a",
    "i want an",
    "i want you to make a",
    "i want you to make an",
    "i want you to build a",
    "i want you to build an",
    "i need a",
    "i need an",
    "i need you to make a",
    "i need you to make an",
    "i need you to build a",
    "i need you to build an",
    "please write code for",
    "please write me code for",
    "please write me the code for",
    "please make a",
    "please make an",
    "please build a",
    "please build an",
    "please create a",
    "please create an",
    "write code for",
    "write a code for",
    "write me code for",
    "write me a code for",
    "write me the code for",
    "write the code for",
    "write code to",
    "write a code to",
    "write me code to",
    "write me the code to",
    "write the code to",
    "give me code for",
    "give me the code for",
    "give me full code for",
    "give full code for",
    "show me code for",
    "show me the code for",
    "source code for",
    "full code for",
    "create code for",
    "create me code for",
    "make code for",
    "make me code for",
    "generate code for",
    "generate me code for",
    "build code for",
    "build me code for",
    "code a",
    "code an",
    "code me a",
    "code me an",
    "make me",
    "make a game",
    "make a web game",
    "make an app",
    "make a app",
    "make a website",
    "make me a game",
    "make me an app",
    "make me a website",
    "build a game",
    "build a web game",
    "build an app",
    "build a app",
    "build a website",
    "create a game",
    "create a web game",
    "create an app",
    "create a app",
    "create a website",
    "develop a game",
    "develop an app",
    "develop a website",
)

CODE_INTENT_WORDS = (
    "code",
    "program",
    "script",
    "app",
    "application",
    "website",
    "web site",
    "webpage",
    "web page",
    "game",
    "html",
    "css",
    "javascript",
    "python",
    "react",
)

BUILD_INTENT_WORDS = (
    "write",
    "make",
    "build",
    "create",
    "generate",
    "develop",
    "program",
    "code",
    "give",
    "show",
)


LANGUAGE_EXTENSIONS = {
    "html": "html",
    "css": "css",
    "javascript": "js",
    "js": "js",
    "python": "py",
    "py": "py",
    "typescript": "ts",
    "ts": "ts",
    "tsx": "tsx",
    "jsx": "jsx",
    "json": "json",
    "markdown": "md",
    "md": "md",
}


def extract_code_request(text: str) -> str | None:
    cleaned = " ".join(text.strip().split())
    normalized = cleaned.lower()

    for wake in ("hey jarvis", "hi jarvis", "hello jarvis", "ok jarvis", "okay jarvis", "jarvis"):
        if normalized.startswith(wake):
            cleaned = cleaned[len(wake) :].strip(" ,:.-")
            normalized = cleaned.lower()
            break

    for trigger in CODE_TRIGGERS:
        index = normalized.find(trigger)
        if index >= 0:
            request = cleaned[index:].strip()
            return request or cleaned

    if _looks_like_code_creation(normalized):
        return cleaned

    return None


def _looks_like_code_creation(normalized: str) -> bool:
    has_build_intent = any(word in normalized for word in BUILD_INTENT_WORDS)
    has_code_intent = any(word in normalized for word in CODE_INTENT_WORDS)
    asks_for_output = any(
        phrase in normalized
        for phrase in ("for me", "me a", "me an", "full code", "source code", "the code", "write me", "make me")
    )

    wants_project = any(phrase in normalized for phrase in ("i want", "i need")) and has_code_intent

    if has_build_intent and has_code_intent:
        return True

    if (asks_for_output or wants_project) and has_code_intent:
        return True

    return False


def create_code_project(user_request: str, model_response: str) -> str:
    spec = _parse_project_spec(model_response)
    project_name = _safe_project_name(spec.get("project_name") or user_request)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    project_dir = CODE_ROOT / f"{stamp}-{project_name}"
    project_dir.mkdir(parents=True, exist_ok=True)

    files = spec.get("files") if isinstance(spec.get("files"), list) else []
    written: list[Path] = []

    for item in files[:MAX_FILES]:
        if not isinstance(item, dict):
            continue

        relative_path = _safe_relative_path(str(item.get("path") or "main.txt"))
        content = str(item.get("content") or "")[:MAX_FILE_CHARS]
        if not content.strip():
            continue

        file_path = project_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8", newline="\n")
        written.append(file_path)

    if not written:
        fallback = project_dir / "README.md"
        fallback.write_text(
            "# JX JARVIS Code Output\n\n"
            f"Request: {user_request}\n\n"
            "Jarvis could not parse a file list, so the raw AI response is below.\n\n"
            "```text\n"
            f"{model_response[:MAX_FILE_CHARS]}\n"
            "```\n",
            encoding="utf-8",
            newline="\n",
        )
        written.append(fallback)

    _write_project_readme(project_dir, user_request, spec.get("summary"), written)
    validation = validate_code_project(project_dir)
    preview = _open_preview(project_dir)
    opened = _open_in_vscode(project_dir)
    file_list = ", ".join(path.name for path in written[:4])
    if len(written) > 4:
        file_list += f", and {len(written) - 4} more"

    open_text = "I opened it in a new VS Code window." if opened else "VS Code was not found in PATH, but the files are ready."
    preview_text = " Browser preview opened." if preview else ""
    return f"Code workspace created: {project_dir}. Files: {file_list}. Validation: {validation}. {open_text}{preview_text}"


def open_code_workspace() -> str:
    CODE_ROOT.mkdir(parents=True, exist_ok=True)
    opened = _open_in_vscode(CODE_ROOT)
    if opened:
        return f"Opened code workspace folder: {CODE_ROOT}"
    return f"Code workspace folder is ready: {CODE_ROOT}. VS Code was not found."


def latest_code_project() -> Path | None:
    if not CODE_ROOT.exists():
        return None
    projects = [path for path in CODE_ROOT.iterdir() if path.is_dir()]
    if not projects:
        return None
    return max(projects, key=lambda path: path.stat().st_mtime)


def open_latest_code_project() -> str:
    project = latest_code_project()
    if not project:
        return "No generated code projects found yet."

    opened = _open_in_vscode(project)
    preview = _open_preview(project)
    if opened and preview:
        return f"Opened latest code project in VS Code and browser: {project}"
    if opened:
        return f"Opened latest code project in VS Code: {project}"
    return f"Latest code project is ready: {project}. VS Code was not found."


def test_latest_code_project() -> str:
    project = latest_code_project()
    if not project:
        return "No generated code projects found yet."
    return f"Latest code project test result for {project.name}: {validate_code_project(project)}"


def validate_code_project(project_dir: Path) -> str:
    checks: list[str] = []
    errors: list[str] = []

    for path in project_dir.rglob("*"):
        if not path.is_file():
            continue

        suffix = path.suffix.lower()
        if suffix == ".py":
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(path)],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            checks.append(path.name)
            if result.returncode != 0:
                errors.append(f"{path.name}: {result.stderr.strip()[:240]}")

        elif suffix == ".json":
            checks.append(path.name)
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as error:
                errors.append(f"{path.name}: {error}")

        elif suffix == ".html":
            checks.append(path.name)
            content = path.read_text(encoding="utf-8", errors="ignore").lower()
            if "<html" not in content and "<!doctype" not in content and "<body" not in content:
                errors.append(f"{path.name}: missing basic HTML structure")

    package_json = project_dir / "package.json"
    if package_json.exists() and (project_dir / "node_modules").exists():
        result = subprocess.run(
            ["npm.cmd", "run", "build"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        checks.append("npm build")
        if result.returncode != 0:
            errors.append(f"npm build: {(result.stderr or result.stdout).strip()[:300]}")

    if errors:
        return "needs attention - " + " | ".join(errors[:3])

    if not checks:
        return "ready - no runnable checks found"

    return f"passed {len(checks)} check(s)"


def _parse_project_spec(text: str) -> dict:
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    files = []
    for index, block in enumerate(re.finditer(r"```([a-zA-Z0-9_+-]*)\s*\n(.*?)```", text, re.DOTALL), start=1):
        language = block.group(1).lower()
        extension = LANGUAGE_EXTENSIONS.get(language, "txt")
        files.append({"path": f"main-{index}.{extension}", "content": block.group(2).strip()})

    return {
        "project_name": "jarvis-code",
        "summary": "Generated code from the assistant response.",
        "files": files,
    }


def _safe_project_name(value: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return (name[:48] or "jarvis-code").strip("-")


def _safe_relative_path(value: str) -> Path:
    cleaned = value.replace("\\", "/").strip().lstrip("/")
    pure = PurePosixPath(cleaned)
    parts = [part for part in pure.parts if part not in ("", ".", "..")]
    if not parts:
        parts = ["main.txt"]
    return Path(*parts)


def _write_project_readme(project_dir: Path, user_request: str, summary: object, written: list[Path]) -> None:
    readme = project_dir / "README.md"
    if readme in written:
        return

    relative_files = "\n".join(f"- {path.relative_to(project_dir)}" for path in written)
    readme.write_text(
        "# JX JARVIS Generated Code\n\n"
        f"Request: {user_request}\n\n"
        f"Summary: {summary or 'Code workspace generated by JX JARVIS.'}\n\n"
        "Files:\n"
        f"{relative_files}\n",
        encoding="utf-8",
        newline="\n",
    )


def _open_preview(project_dir: Path) -> bool:
    for name in ("index.html", "app.html"):
        candidate = project_dir / name
        if candidate.exists():
            webbrowser.open(candidate.resolve().as_uri())
            return True
    return False


def _open_in_vscode(path: Path) -> bool:
    commands = ["code.cmd", "code"]
    local_app_data = os.getenv("LOCALAPPDATA")
    program_files = os.getenv("ProgramFiles")

    if local_app_data:
        commands.append(str(Path(local_app_data) / "Programs" / "Microsoft VS Code" / "Code.exe"))
    if program_files:
        commands.append(str(Path(program_files) / "Microsoft VS Code" / "Code.exe"))

    for command in commands:
        try:
            subprocess.Popen(
                [command, "-n", str(path)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
            )
            return True
        except (FileNotFoundError, OSError):
            continue

    return False

import json
import subprocess
from pathlib import Path

from api.memory_storage import recent_memories, remember_event
from api.permissions import evaluate_permission


CODE_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".py", ".html", ".css", ".json", ".md", ".cjs", ".mjs"}


def latest_project_path() -> Path | None:
    for memory in recent_memories(limit=25, kind="projects"):
        path = (memory.get("metadata") or {}).get("path")
        if path and Path(path).exists():
            return Path(path)
    return None


def analyze_project(path: str | None = None) -> dict:
    root = Path(path).expanduser().resolve() if path else latest_project_path()
    if not root or not root.exists():
        return {"ok": False, "error": "No local coding project is available yet."}

    decision = evaluate_permission("file.read", f"analyze project {root}", path=str(root))
    if not decision.allowed:
        return {"ok": False, "error": decision.message}

    files = []
    for item in root.rglob("*"):
        if item.is_file() and item.suffix.lower() in CODE_EXTENSIONS:
            try:
                rel = str(item.relative_to(root))
            except ValueError:
                rel = str(item)
            files.append({"path": rel, "size": item.stat().st_size, "extension": item.suffix.lower()})
        if len(files) >= 220:
            break

    package = _read_json(root / "package.json")
    summary = {
        "ok": True,
        "path": str(root),
        "fileCount": len(files),
        "topFiles": files[:40],
        "package": {
            "name": package.get("name", "") if package else "",
            "scripts": package.get("scripts", {}) if package else {},
            "dependencies": sorted((package.get("dependencies") or {}).keys())[:30] if package else [],
        },
        "framework": _detect_framework(files, package),
    }
    remember_event("projects", f"Analyzed {root.name}", f"Project has {len(files)} code file(s).", {"path": str(root)})
    return summary


def run_project_script(path: str | None = None, script: str = "build") -> dict:
    root = Path(path).expanduser().resolve() if path else latest_project_path()
    if not root or not root.exists():
        return {"ok": False, "error": "No local coding project is available yet."}

    decision = evaluate_permission("terminal.run", f"run npm {script} in {root}", path=str(root), command=f"npm run {script}")
    if not decision.allowed:
        return {"ok": False, "error": decision.message}

    package = _read_json(root / "package.json")
    if not package or script not in (package.get("scripts") or {}):
        return {"ok": False, "error": f"Project has no npm script named {script}."}

    result = subprocess.run(
        ["npm.cmd" if _is_windows() else "npm", "run", script],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    output = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
    ok = result.returncode == 0
    remember_event(
        "projects",
        f"Ran npm {script} in {root.name}",
        output[-5000:] or f"Exit code {result.returncode}",
        {"path": str(root), "script": script, "ok": ok},
    )
    return {"ok": ok, "exitCode": result.returncode, "output": output[-12000:], "path": str(root), "script": script}


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _detect_framework(files: list[dict], package: dict | None) -> str:
    names = {item["path"].lower().replace("\\", "/") for item in files}
    dependencies = set(((package or {}).get("dependencies") or {}).keys())
    if "react" in dependencies or any(path.endswith(".jsx") or path.endswith(".tsx") for path in names):
        return "React"
    if any(path.endswith(".py") for path in names):
        return "Python"
    if any(path.endswith("index.html") for path in names):
        return "HTML/CSS/JS"
    return "Unknown"


def _is_windows() -> bool:
    return __import__("platform").system().lower() == "windows"

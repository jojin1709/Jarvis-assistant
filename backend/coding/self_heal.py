from __future__ import annotations

import re
from pathlib import Path

from terminal.service import terminal_service
from workspace.indexer import scan_workspace


def run_self_healing_loop(project_path: str | Path, install: bool = True, max_attempts: int = 3) -> dict:
    root = Path(project_path).expanduser().resolve()
    attempts = []
    if install:
        attempts.extend(_run_commands(root, ["npm install", "npm --prefix frontend install", "npm --prefix backend install"]))

    for attempt in range(1, max_attempts + 1):
        jobs = _run_commands(root, ["npm --prefix frontend run build", "npm --prefix backend run check"])
        attempts.extend(jobs)
        failures = [job for job in jobs if job.get("status") != "completed"]
        if not failures:
            return {"ok": True, "path": str(root), "attempts": attempts, "workspace": scan_workspace(root).as_dict()}
        patched = _apply_known_patch(root, "\n".join((job.get("stderr") or job.get("stdout") or "") for job in failures))
        attempts.append({"status": "patched" if patched else "unpatched", "stdout": patched or "No known automatic patch matched."})
        if not patched:
            break
    return {"ok": False, "path": str(root), "attempts": attempts, "workspace": scan_workspace(root).as_dict()}


def _run_commands(root: Path, commands: list[str]) -> list[dict]:
    results = []
    for command in commands:
        job = terminal_service.run_sync(command, cwd=root, timeout=240)
        results.append(job.as_dict())
    return results


def _apply_known_patch(root: Path, error_text: str) -> str:
    lowered = error_text.lower()
    if "could not resolve" in lowered and "@vitejs/plugin-react" in lowered:
        return "Dependency @vitejs/plugin-react is declared; rerun install after network/dependency availability is restored."

    main = root / "frontend" / "src" / "main.jsx"
    if main.exists() and "react is not defined" in lowered:
        content = main.read_text(encoding="utf-8")
        if not re.search(r"import\s+React\s+from", content):
            main.write_text('import React from "react";\n' + content, encoding="utf-8", newline="\n")
            return "Patched frontend/src/main.jsx by adding React import."

    server = root / "backend" / "server.js"
    if server.exists() and "cannot use import statement" in lowered:
        package_json = root / "backend" / "package.json"
        if package_json.exists():
            import json

            data = json.loads(package_json.read_text(encoding="utf-8"))
            data["type"] = "module"
            package_json.write_text(json.dumps(data, indent=2), encoding="utf-8", newline="\n")
            return "Patched backend/package.json by enabling ES modules."
    return ""

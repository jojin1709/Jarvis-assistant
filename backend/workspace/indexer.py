from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


CODE_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".py", ".html", ".css", ".json", ".md", ".yml", ".yaml", ".toml"}


@dataclass
class WorkspaceIndex:
    root: str
    file_count: int
    frameworks: list[str] = field(default_factory=list)
    package_scripts: dict[str, str] = field(default_factory=dict)
    important_files: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "root": self.root,
            "fileCount": self.file_count,
            "frameworks": self.frameworks,
            "packageScripts": self.package_scripts,
            "importantFiles": self.important_files,
        }


def scan_workspace(root: str | Path, limit: int = 700) -> WorkspaceIndex:
    path = Path(root).expanduser().resolve()
    files: list[Path] = []
    if path.exists():
        for item in path.rglob("*"):
            if len(files) >= limit:
                break
            if item.is_file() and item.suffix.lower() in CODE_SUFFIXES and "node_modules" not in item.parts:
                files.append(item)

    package = _read_json(path / "package.json")
    package_scripts = package.get("scripts", {}) if isinstance(package, dict) else {}
    names = {str(item.relative_to(path)).replace("\\", "/").lower() for item in files}
    dependencies = set((package.get("dependencies") or {}).keys()) if isinstance(package, dict) else set()

    frameworks = []
    if "react" in dependencies or any(name.endswith((".jsx", ".tsx")) for name in names):
        frameworks.append("React")
    if "express" in dependencies:
        frameworks.append("Express")
    if "mongoose" in dependencies or "mongodb" in dependencies:
        frameworks.append("MongoDB")
    if any(name.endswith(".py") for name in names):
        frameworks.append("Python")
    if "vite.config.js" in names or "vite.config.ts" in names:
        frameworks.append("Vite")

    important = [
        name
        for name in sorted(names)
        if name in {"package.json", "vite.config.js", "src/app.jsx", "src/main.jsx", "server.js", "backend/server.js", "README.md".lower()}
        or name.endswith((".config.js", ".config.ts"))
    ][:80]
    return WorkspaceIndex(str(path), len(files), frameworks, package_scripts, important)


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

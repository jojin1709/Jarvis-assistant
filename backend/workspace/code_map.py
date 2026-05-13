from __future__ import annotations

import ast
import json
import re
from pathlib import Path


def build_code_map(root: str | Path) -> dict:
    base = Path(root).expanduser().resolve()
    if not base.exists():
        return {"ok": False, "error": f"Path does not exist: {base}"}
    files = [path for path in base.rglob("*") if path.is_file() and path.suffix.lower() in {".py", ".js", ".jsx", ".ts", ".tsx", ".json"}]
    nodes = []
    edges = []
    for path in files[:600]:
        rel = str(path.relative_to(base))
        imports = _imports(path)
        nodes.append({"id": rel, "type": path.suffix.lower().lstrip("."), "imports": imports})
        for target in imports:
            edges.append({"from": rel, "to": target, "kind": "imports"})
    return {"ok": True, "root": str(base), "files": len(files), "nodes": nodes, "edges": edges[:2000], "services": _service_map(base)}


def _imports(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if path.suffix == ".py":
            tree = ast.parse(text)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
            return imports[:80]
        if path.suffix == ".json" and path.name == "package.json":
            data = json.loads(text)
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            return list(deps)[:120]
        matches = re.findall(r"(?:from|require\()\s*['\"]([^'\"]+)['\"]|import\s+['\"]([^'\"]+)['\"]", text)
        return [left or right for left, right in matches][:80]
    except Exception:
        return []


def _service_map(base: Path) -> list[dict]:
    services = []
    for package in base.rglob("package.json"):
        try:
            data = json.loads(package.read_text(encoding="utf-8"))
            services.append({"name": data.get("name") or package.parent.name, "path": str(package.parent), "scripts": data.get("scripts", {})})
        except Exception:
            continue
    return services

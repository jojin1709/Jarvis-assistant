from __future__ import annotations

from workspace.code_map import build_code_map


def generate_architecture_doc(path: str = ".") -> str:
    code_map = build_code_map(path)
    services = code_map.get("services", [])
    lines = ["# Architecture Overview", "", f"Root: `{code_map.get('root', path)}`", "", "## Services"]
    lines.extend(f"- `{service.get('name')}` at `{service.get('path')}`" for service in services)
    lines.append("")
    lines.append(f"Indexed files: {code_map.get('files', 0)}")
    return "\n".join(lines)

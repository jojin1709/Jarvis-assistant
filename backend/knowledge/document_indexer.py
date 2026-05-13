from __future__ import annotations

from pathlib import Path

from knowledge.vector_store import add_document


INDEX_EXTENSIONS = {".md", ".txt", ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".yml", ".yaml"}


def index_path(path: str | Path, source: str = "workspace", limit: int = 400) -> dict:
    root = Path(path).expanduser().resolve()
    if not root.exists():
        return {"ok": False, "error": f"Path does not exist: {root}"}
    files = [root] if root.is_file() else [item for item in root.rglob("*") if item.is_file() and item.suffix.lower() in INDEX_EXTENSIONS]
    indexed = []
    for file_path in files[:limit]:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if not content.strip():
                continue
            title = str(file_path.relative_to(root if root.is_dir() else root.parent))
            indexed.append(add_document(title, content[:20000], source=source, metadata={"path": str(file_path)}))
        except Exception:
            continue
    return {"ok": True, "root": str(root), "indexed": indexed, "count": len(indexed)}

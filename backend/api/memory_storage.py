import json
import hashlib
import shutil
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path

from api.permissions import log_activity


RUNTIME_DIR = Path(__file__).resolve().parents[1] / "runtime"
CONFIG_PATH = RUNTIME_DIR / "memory_storage.json"
DEFAULT_MEMORY_ROOT = Path.home() / "Desktop" / "Jarvis Brain"
MEMORY_DIRS = (
    "conversations",
    "workflows",
    "projects",
    "preferences",
    "voice",
    "browser",
    "automation",
    "cache",
    "embeddings",
    "logs",
    "backups",
)


def memory_storage_state() -> dict:
    root = configured_memory_root()
    initialized = root.exists() and (root / "brain.sqlite3").exists()
    usage = memory_usage(root) if root.exists() else {"bytes": 0, "display": "0 B", "files": 0}
    return {
        "path": str(root),
        "initialized": initialized,
        "structure": list(MEMORY_DIRS),
        "database": str(root / "brain.sqlite3"),
        "usage": usage,
        "recent": recent_memories(limit=10) if initialized else [],
    }


def setup_memory_storage(path: str | None = None, create_default: bool = True) -> dict:
    root = _safe_root(path) if path else DEFAULT_MEMORY_ROOT
    if create_default:
        root.mkdir(parents=True, exist_ok=True)
    if not root.exists():
        raise FileNotFoundError(f"Memory folder does not exist: {root}")

    for name in MEMORY_DIRS:
        (root / name).mkdir(parents=True, exist_ok=True)

    _save_config({"path": str(root), "updated_at": datetime.now().isoformat(timespec="seconds")})
    _init_database(root)
    remember_event(
        "preferences",
        "Memory storage configured",
        f"Jarvis memory storage is configured at {root}",
        {"path": str(root)},
    )
    log_activity(f"Memory storage configured: {root}", "success", "memory")
    return memory_storage_state()


def configured_memory_root() -> Path:
    data = _load_config()
    path = str(data.get("path") or "").strip()
    return _safe_root(path) if path else DEFAULT_MEMORY_ROOT


def remember_event(kind: str, title: str, content: str, metadata: dict | None = None) -> None:
    root = configured_memory_root()
    if not root.exists():
        setup_memory_storage(str(root))

    safe_kind = kind if kind in MEMORY_DIRS else "cache"
    timestamp = datetime.now().isoformat(timespec="seconds")
    metadata = metadata or {}
    db_path = root / "brain.sqlite3"
    try:
        _init_database(root)
    except sqlite3.OperationalError:
        pass

    try:
        columns = _memory_columns(db_path)
        with sqlite3.connect(db_path) as connection:
            if "embedding_json" in columns:
                connection.execute(
                    """
                    insert into memories(kind, title, content, metadata_json, embedding_json, created_at, updated_at)
                    values (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        safe_kind,
                        title[:240],
                        content[:12000],
                        json.dumps(metadata),
                        json.dumps(_text_embedding(f"{safe_kind} {title} {content}")),
                        timestamp,
                        timestamp,
                    ),
                )
            else:
                connection.execute(
                    """
                    insert into memories(kind, title, content, metadata_json, created_at, updated_at)
                    values (?, ?, ?, ?, ?, ?)
                    """,
                    (safe_kind, title[:240], content[:12000], json.dumps(metadata), timestamp, timestamp),
                )
            connection.commit()
    except sqlite3.Error:
        pass

    record_path = root / safe_kind / f"{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.json"
    try:
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(
            json.dumps(
                {
                    "kind": safe_kind,
                    "title": title,
                    "content": content,
                    "metadata": metadata,
                    "created_at": timestamp,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    except OSError:
        pass


def remember_conversation(user_text: str, assistant_text: str, metadata: dict | None = None) -> None:
    remember_event(
        "conversations",
        user_text[:160] or "Conversation",
        f"User: {user_text}\n\nJarvis: {assistant_text}",
        metadata or {},
    )


def remember_project(name: str, path: str, summary: str) -> None:
    remember_event("projects", name, summary, {"path": path})


def recent_memories(limit: int = 20, kind: str | None = None) -> list[dict[str, object]]:
    root = configured_memory_root()
    db_path = root / "brain.sqlite3"
    if not db_path.exists():
        return []
    try:
        _init_database(root)
    except sqlite3.OperationalError:
        pass

    columns = _memory_columns(db_path)
    embedding_select = "embedding_json" if "embedding_json" in columns else "'' as embedding_json"
    query = f"select id, kind, title, content, metadata_json, created_at, {embedding_select} from memories"
    values: tuple = ()
    if kind:
        query += " where kind = ?"
        values = (kind,)
    query += " order by id desc limit ?"
    values = (*values, limit)

    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(query, values).fetchall()

    memories = []
    for row in rows:
        metadata = {}
        try:
            metadata = json.loads(row[4] or "{}")
        except json.JSONDecodeError:
            metadata = {}
        memories.append(
            {
                "id": row[0],
                "kind": row[1],
                "title": row[2],
                "content": row[3],
                "metadata": metadata,
                "created_at": row[5],
                "embedding": _load_embedding(row[6] if len(row) > 6 else ""),
            }
        )
    return memories


def search_memories(query: str, limit: int = 12, kind: str | None = None) -> list[dict[str, object]]:
    tokens = [token for token in _search_tokens(query) if len(token) >= 2]
    if not tokens:
        return []

    root = configured_memory_root()
    db_path = root / "brain.sqlite3"
    if not db_path.exists():
        return []

    rows = recent_memories(limit=400, kind=kind)
    query_embedding = _text_embedding(query)
    scored: list[tuple[int, dict[str, object]]] = []
    for memory in rows:
        haystack = " ".join(
            str(value or "")
            for value in (memory.get("kind"), memory.get("title"), memory.get("content"), json.dumps(memory.get("metadata") or {}))
        ).lower()
        keyword_score = sum(3 if token in str(memory.get("title", "")).lower() else 1 for token in tokens if token in haystack)
        embedding_score = int(_cosine(query_embedding, memory.get("embedding") if isinstance(memory.get("embedding"), list) else []) * 100)
        score = keyword_score * 10 + embedding_score
        if score > 0:
            scored.append((score, memory))

    scored.sort(key=lambda item: (item[0], str(item[1].get("created_at") or "")), reverse=True)
    return [memory for _score, memory in scored[:limit]]


def backup_memory() -> dict:
    root = configured_memory_root()
    if not root.exists():
        setup_memory_storage(str(root))
    backup_dir = root / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / f"jarvis-memory-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in root.rglob("*"):
            if path == target or target in path.parents:
                continue
            if path.is_file():
                archive.write(path, path.relative_to(root))
    log_activity(f"Memory backup created: {target}", "success", "memory")
    return {"path": str(target), "size": target.stat().st_size}


def clear_brain_memory() -> dict:
    root = configured_memory_root()
    for name in MEMORY_DIRS:
        folder = root / name
        if folder.exists() and name != "backups":
            shutil.rmtree(folder)
            folder.mkdir(parents=True, exist_ok=True)
    db_path = root / "brain.sqlite3"
    if db_path.exists():
        db_path.unlink()
    _init_database(root)
    log_activity("Brain memory cleared.", "warning", "memory")
    return memory_storage_state()


def memory_usage(root: Path | None = None) -> dict[str, object]:
    root = root or configured_memory_root()
    total = 0
    files = 0
    if root.exists():
        for path in root.rglob("*"):
            if path.is_file():
                files += 1
                total += path.stat().st_size
    return {"bytes": total, "display": _format_bytes(total), "files": files}


def _init_database(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(root / "brain.sqlite3") as connection:
        connection.execute(
            """
            create table if not exists memories (
                id integer primary key autoincrement,
                kind text not null,
                title text not null,
                content text not null,
                metadata_json text,
                embedding_json text,
                created_at text not null,
                updated_at text not null
            )
            """
        )
        columns = {row[1] for row in connection.execute("pragma table_info(memories)").fetchall()}
        if "embedding_json" not in columns:
            connection.execute("alter table memories add column embedding_json text")
        connection.execute("create index if not exists idx_memories_kind on memories(kind)")
        connection.execute("create index if not exists idx_memories_created_at on memories(created_at)")
        connection.commit()


def _memory_columns(db_path: Path) -> set[str]:
    try:
        with sqlite3.connect(db_path) as connection:
            return {row[1] for row in connection.execute("pragma table_info(memories)").fetchall()}
    except sqlite3.Error:
        return set()


def _safe_root(value: str) -> Path:
    cleaned = str(value).strip().strip('"')
    if cleaned.startswith("~"):
        return Path(cleaned).expanduser().resolve()
    return Path(cleaned).expanduser().resolve()


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_config(data: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _format_bytes(value: int) -> str:
    size = float(value)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{int(value)} B"


def _search_tokens(value: str) -> list[str]:
    return [token.strip().lower() for token in "".join(ch if ch.isalnum() else " " for ch in value).split()]


def _text_embedding(value: str, dimensions: int = 64) -> list[float]:
    vector = [0.0] * dimensions
    for token in _search_tokens(value):
        slot = int(hashlib.sha256(token.encode("utf-8")).hexdigest()[:8], 16) % dimensions
        vector[slot] += 1.0
    magnitude = sum(item * item for item in vector) ** 0.5
    if not magnitude:
        return vector
    return [round(item / magnitude, 6) for item in vector]


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))


def _load_embedding(value: object) -> list[float]:
    try:
        parsed = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [float(item) for item in parsed if isinstance(item, (int, float))]

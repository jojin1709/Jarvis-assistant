from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from knowledge.embedding_engine import cosine, embed_text


DB_PATH = Path(__file__).resolve().parents[1] / "runtime" / "knowledge.sqlite3"


def add_document(title: str, content: str, source: str = "manual", metadata: dict | None = None) -> dict:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    vector = embed_text(f"{title}\n{content}")
    with _connect() as conn:
        _init(conn)
        cursor = conn.execute(
            """
            INSERT INTO documents(title, content, source, metadata, embedding, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, content, source, json.dumps(metadata or {}), json.dumps(vector), datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
        return {"id": cursor.lastrowid, "title": title, "source": source}


def search_documents(query: str, limit: int = 8) -> list[dict]:
    query_vector = embed_text(query)
    with _connect() as conn:
        _init(conn)
        rows = conn.execute("SELECT id,title,content,source,metadata,embedding,created_at FROM documents").fetchall()
    scored = []
    for row in rows:
        vector = json.loads(row["embedding"] or "[]")
        scored.append(
            {
                "id": row["id"],
                "title": row["title"],
                "content": row["content"],
                "source": row["source"],
                "metadata": json.loads(row["metadata"] or "{}"),
                "createdAt": row["created_at"],
                "score": round(cosine(query_vector, vector), 4),
            }
        )
    return sorted(scored, key=lambda item: item["score"], reverse=True)[:limit]


def knowledge_stats() -> dict:
    with _connect() as conn:
        _init(conn)
        count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        sources = conn.execute("SELECT source, COUNT(*) count FROM documents GROUP BY source").fetchall()
    return {"documents": count, "sources": [{"source": row["source"], "count": row["count"]} for row in sources]}


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS documents(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT NOT NULL,
            metadata TEXT NOT NULL,
            embedding TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

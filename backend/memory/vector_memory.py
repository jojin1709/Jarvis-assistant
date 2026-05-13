from __future__ import annotations

from knowledge.vector_store import add_document, search_documents


def remember_vector(title: str, content: str, source: str = "agentic", metadata: dict | None = None) -> dict:
    return add_document(title, content, source=source, metadata=metadata)


def recall_vector(query: str, limit: int = 8) -> list[dict]:
    return search_documents(query, limit=limit)

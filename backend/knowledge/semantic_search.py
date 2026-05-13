from __future__ import annotations

from knowledge.vector_store import knowledge_stats, search_documents


def search_knowledge(query: str, limit: int = 8) -> dict:
    results = search_documents(query, limit=limit)
    return {"ok": True, "query": query, "results": results, "stats": knowledge_stats()}

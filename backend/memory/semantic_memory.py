from __future__ import annotations

from api.memory_storage import search_memories
from memory.vector_memory import recall_vector


def semantic_recall(query: str, limit: int = 8) -> dict:
    return {"memories": search_memories(query, limit=limit), "knowledge": recall_vector(query, limit=limit)}

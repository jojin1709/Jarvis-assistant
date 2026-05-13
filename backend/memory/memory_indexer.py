from __future__ import annotations

from knowledge.document_indexer import index_path


def index_memory_source(path: str, source: str = "memory") -> dict:
    return index_path(path, source=source)

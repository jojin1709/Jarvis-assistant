from __future__ import annotations

from functools import lru_cache
import hashlib
import math


DIMENSIONS = 64
TRANSFORMER_MODEL = "all-MiniLM-L6-v2"


def embed_text(text: str) -> list[float]:
    model = _sentence_transformer()
    if model is not None:
        return model.encode(text or "", normalize_embeddings=True).tolist()
    return _fallback_embed_text(text)


def cosine(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    return sum(left[index] * right[index] for index in range(size))


@lru_cache(maxsize=1)
def _sentence_transformer():
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(TRANSFORMER_MODEL)
    except Exception:
        return None


def _fallback_embed_text(text: str) -> list[float]:
    vector = [0.0] * DIMENSIONS
    tokens = [_normalize_token(token) for token in _tokens(text)]
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % DIMENSIONS
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [round(value / norm, 6) for value in vector]


def _tokens(text: str) -> list[str]:
    import re

    return re.findall(r"[a-zA-Z0-9_./:-]{2,}", text or "")


def _normalize_token(token: str) -> str:
    synonyms = {
        "built": "created",
        "build": "created",
        "made": "created",
        "maker": "creator",
        "author": "creator",
        "founded": "created",
        "developed": "created",
        "developer": "creator",
    }
    lowered = token.lower()
    return synonyms.get(lowered, lowered)

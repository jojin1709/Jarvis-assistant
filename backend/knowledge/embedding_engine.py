from __future__ import annotations

import hashlib
import math


DIMENSIONS = 64


def embed_text(text: str) -> list[float]:
    vector = [0.0] * DIMENSIONS
    tokens = [token.lower() for token in _tokens(text)]
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % DIMENSIONS
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [round(value / norm, 6) for value in vector]


def cosine(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    return sum(left[index] * right[index] for index in range(size))


def _tokens(text: str) -> list[str]:
    import re

    return re.findall(r"[a-zA-Z0-9_./:-]{2,}", text or "")

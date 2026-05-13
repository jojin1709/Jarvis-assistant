from __future__ import annotations


def summarize_text(text: str, max_sentences: int = 5) -> dict:
    import re

    sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", text or "") if len(item.strip()) > 20]
    keywords = _keywords(text)
    selected = sentences[:max_sentences]
    return {"summary": " ".join(selected)[:1800], "keywords": keywords}


def _keywords(text: str) -> list[str]:
    import re
    from collections import Counter

    stop = {"the", "and", "for", "with", "that", "this", "from", "are", "was", "you", "your", "into", "have"}
    tokens = [token.lower() for token in re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{3,}", text or "") if token.lower() not in stop]
    return [token for token, _count in Counter(tokens).most_common(12)]

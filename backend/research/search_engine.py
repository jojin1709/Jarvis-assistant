from __future__ import annotations

from urllib.parse import quote_plus
from urllib.request import Request, urlopen


def web_search(query: str, limit: int = 5) -> dict:
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        request = Request(url, headers={"User-Agent": "JX-Jarvis/1.0"})
        with urlopen(request, timeout=12) as response:
            html = response.read().decode("utf-8", errors="ignore")
        return {"ok": True, "query": query, "results": _parse_results(html, limit)}
    except Exception as error:
        return {"ok": False, "query": query, "error": str(error), "results": []}


def _parse_results(html: str, limit: int) -> list[dict]:
    import re
    from html import unescape

    rows = []
    pattern = re.compile(r'<a rel="nofollow" class="result__a" href="(?P<url>[^"]+)".*?>(?P<title>.*?)</a>', re.S)
    for match in pattern.finditer(html):
        title = re.sub(r"<.*?>", "", match.group("title"))
        rows.append({"title": unescape(title), "url": unescape(match.group("url"))})
        if len(rows) >= limit:
            break
    return rows

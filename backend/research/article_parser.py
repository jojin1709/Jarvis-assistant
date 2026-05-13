from __future__ import annotations

from urllib.request import Request, urlopen


def fetch_article(url: str) -> dict:
    try:
        request = Request(url, headers={"User-Agent": "JX-Jarvis/1.0"})
        with urlopen(request, timeout=12) as response:
            html = response.read().decode("utf-8", errors="ignore")
        return {"ok": True, "url": url, "text": _clean_html(html)}
    except Exception as error:
        return {"ok": False, "url": url, "error": str(error), "text": ""}


def _clean_html(html: str) -> str:
    import re
    from html import unescape

    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<.*?>", " ", html)
    return re.sub(r"\s+", " ", unescape(text)).strip()[:20000]

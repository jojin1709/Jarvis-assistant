import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "JX-Jarvis/1.0 (+https://github.com/jojin1709/Jarvis-assistant)",
}


def post_json(url: str, payload: dict, headers: dict | None = None, timeout: int = 60) -> tuple[dict, float]:
    started = time.perf_counter()
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={**DEFAULT_HEADERS, **(headers or {})},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(_format_http_error(error.code, details)) from error
    except URLError as error:
        raise RuntimeError(str(error.reason)) from error
    return json.loads(raw), round((time.perf_counter() - started) * 1000, 1)


def get_json(url: str, headers: dict | None = None, timeout: int = 8) -> tuple[dict, float]:
    started = time.perf_counter()
    request = Request(url, headers={**DEFAULT_HEADERS, **(headers or {})}, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(_format_http_error(error.code, details)) from error
    except URLError as error:
        raise RuntimeError(str(error.reason)) from error
    return json.loads(raw), round((time.perf_counter() - started) * 1000, 1)


def _format_http_error(status_code: int, body: str) -> str:
    compact = " ".join(str(body or "").split())
    if "error code: 1010" in compact.lower():
        return f"HTTP {status_code}: provider edge protection blocked the request (error code 1010)."
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return f"HTTP {status_code}: {compact[:500]}"
    error = data.get("error") if isinstance(data, dict) else None
    if isinstance(error, dict):
        message = error.get("message") or error.get("code") or error.get("type")
        if message:
            return f"HTTP {status_code}: {message}"
    if isinstance(error, str):
        return f"HTTP {status_code}: {error}"
    message = data.get("message") if isinstance(data, dict) else ""
    return f"HTTP {status_code}: {message or compact[:500]}"

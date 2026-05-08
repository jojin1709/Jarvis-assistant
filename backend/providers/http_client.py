import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def post_json(url: str, payload: dict, headers: dict | None = None, timeout: int = 60) -> tuple[dict, float]:
    started = time.perf_counter()
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {error.code}: {details}") from error
    except URLError as error:
        raise RuntimeError(str(error.reason)) from error
    return json.loads(raw), round((time.perf_counter() - started) * 1000, 1)


def get_json(url: str, headers: dict | None = None, timeout: int = 8) -> tuple[dict, float]:
    started = time.perf_counter()
    request = Request(url, headers=headers or {}, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {error.code}: {details}") from error
    except URLError as error:
        raise RuntimeError(str(error.reason)) from error
    return json.loads(raw), round((time.perf_counter() - started) * 1000, 1)

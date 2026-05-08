import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import settings


def _deepseek_url() -> str:
    return f"{settings.deepseek_base_url.rstrip('/')}/chat/completions"


def chat_deepseek_messages(
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 700,
    response_format: dict[str, str] | None = None,
) -> str:
    if not settings.deepseek_api_key:
        raise RuntimeError("DeepSeek API key is not configured.")

    payload = {
        "model": settings.deepseek_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format
    if settings.deepseek_thinking in {"enabled", "disabled"}:
        payload["thinking"] = {"type": settings.deepseek_thinking}

    request = Request(
        _deepseek_url(),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek API request failed with HTTP {error.code}: {details}") from error
    except URLError as error:
        raise RuntimeError(f"DeepSeek API request failed: {error.reason}") from error

    data = json.loads(raw)
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("DeepSeek API returned no choices.")

    message = choices[0].get("message") or {}
    content = str(message.get("content") or "").strip()
    if not content:
        raise RuntimeError("DeepSeek API returned an empty response.")
    return content

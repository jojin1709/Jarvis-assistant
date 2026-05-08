import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import settings


def _nvidia_url() -> str:
    return f"{settings.nvidia_base_url.rstrip('/')}/chat/completions"


def chat_nvidia_messages(
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 700,
    response_format: dict[str, str] | None = None,
) -> str:
    if not settings.nvidia_api_key:
        raise RuntimeError("NVIDIA API key is not configured.")

    payload = {
        "model": settings.nvidia_model,
        "messages": messages,
        "temperature": min(max(temperature, 0), 1),
        "top_p": settings.nvidia_top_p,
        "max_tokens": max_tokens,
        "stream": False,
        "extra_body": {"chat_template_kwargs": {"thinking": settings.nvidia_thinking}},
    }
    if response_format:
        payload["response_format"] = response_format

    request = Request(
        _nvidia_url(),
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.nvidia_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"NVIDIA API request failed with HTTP {error.code}: {details}") from error
    except URLError as error:
        raise RuntimeError(f"NVIDIA API request failed: {error.reason}") from error

    data = json.loads(raw)
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("NVIDIA API returned no choices.")

    message = choices[0].get("message") or {}
    content = str(message.get("content") or "").strip()
    if not content:
        raise RuntimeError("NVIDIA API returned an empty response.")
    return content

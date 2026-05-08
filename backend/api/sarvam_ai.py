import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from api.groq_ai import CODE_PROJECT_PROMPT, SYSTEM_PROMPT
from app.config import settings


def _sarvam_url() -> str:
    return f"{settings.sarvam_base_url.rstrip('/')}/v1/chat/completions"


def chat_sarvam_messages(
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 700,
    response_format: dict[str, str] | None = None,
) -> str:
    if not settings.sarvam_api_key:
        raise RuntimeError("Sarvam API key is not configured.")

    payload = {
        "model": settings.sarvam_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format

    encoded = json.dumps(payload).encode("utf-8")
    request = Request(
        _sarvam_url(),
        data=encoded,
        headers={
            "Authorization": f"Bearer {settings.sarvam_api_key}",
            "api-subscription-key": settings.sarvam_api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=45) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Sarvam API request failed with HTTP {error.code}: {details}") from error
    except URLError as error:
        raise RuntimeError(f"Sarvam API request failed: {error.reason}") from error

    data = json.loads(raw)
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("Sarvam API returned no choices.")

    message = choices[0].get("message") or {}
    content = str(message.get("content") or "").strip()
    if not content:
        raise RuntimeError("Sarvam API returned an empty response.")
    return content


def ask_sarvam(user_text: str, language_instruction: str = "Reply in English.") -> str:
    if not settings.sarvam_api_key:
        return (
            "Sarvam API key is not configured. Add SARVAM_API_KEY to your .env file, "
            "then restart JX JARVIS."
        )

    return chat_sarvam_messages(
        messages=[
            {"role": "system", "content": f"{SYSTEM_PROMPT.strip()}\n{language_instruction}".strip()},
            {"role": "user", "content": user_text},
        ],
        temperature=0.72,
        max_tokens=700,
    )


def ask_sarvam_code_project(user_text: str) -> str:
    if not settings.sarvam_api_key:
        return (
            '{"project_name":"missing-sarvam-key","summary":"Sarvam API key is not configured.",'
            '"files":[{"path":"README.md","content":"Add SARVAM_API_KEY to .env, restart JX JARVIS, then ask again."}]}'
        )

    return chat_sarvam_messages(
        messages=[
            {"role": "system", "content": CODE_PROJECT_PROMPT.strip()},
            {"role": "user", "content": user_text},
        ],
        temperature=0.35,
        max_tokens=5600,
    )

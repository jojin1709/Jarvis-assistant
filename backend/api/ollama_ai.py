import json
import urllib.error
import urllib.request


def chat_ollama_messages(
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 700,
    response_format: dict[str, str] | None = None,
) -> str:
    from app.config import settings

    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    request = urllib.request.Request(
        f"{settings.ollama_base_url.rstrip('/')}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as error:
        raise RuntimeError("Ollama is not reachable. Start Ollama locally and pull the selected model.") from error

    return ((data.get("message") or {}).get("content") or "").strip() or "Ollama returned an empty response."

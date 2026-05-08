from providers.http_client import get_json, post_json


def chat(messages: list[dict[str, str]], api_key: str, model: str, temperature: float, max_tokens: int, response_format=None, base_url: str = "http://127.0.0.1:11434") -> tuple[str, float]:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    data, latency = post_json(f"{base_url.rstrip('/')}/api/chat", payload, timeout=90)
    content = ((data.get("message") or {}).get("content") or "").strip()
    if not content:
        raise RuntimeError("Ollama returned an empty response.")
    return content, latency


def list_models(base_url: str = "http://127.0.0.1:11434") -> tuple[list[dict], float]:
    data, latency = get_json(f"{base_url.rstrip('/')}/api/tags", timeout=4)
    return data.get("models") or [], latency

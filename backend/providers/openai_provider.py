from providers.http_client import post_json


def chat(messages: list[dict[str, str]], api_key: str, model: str, temperature: float, max_tokens: int, response_format=None, base_url: str = "https://api.openai.com/v1") -> tuple[str, float]:
    payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    if response_format:
        payload["response_format"] = response_format
    data, latency = post_json(
        f"{base_url.rstrip('/')}/chat/completions",
        payload,
        {"Authorization": f"Bearer {api_key}"},
    )
    return _content(data), latency


def _content(data: dict) -> str:
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("Provider returned no choices.")
    content = ((choices[0].get("message") or {}).get("content") or "").strip()
    if not content:
        raise RuntimeError("Provider returned an empty response.")
    return content

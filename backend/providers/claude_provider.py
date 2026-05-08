from providers.http_client import post_json


def chat(messages: list[dict[str, str]], api_key: str, model: str, temperature: float, max_tokens: int, response_format=None) -> tuple[str, float]:
    system = "\n".join(message["content"] for message in messages if message.get("role") == "system")
    claude_messages = [
        {"role": "assistant" if message.get("role") == "assistant" else "user", "content": message.get("content", "")}
        for message in messages
        if message.get("role") != "system"
    ]
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": claude_messages,
    }
    if system:
        payload["system"] = system
    data, latency = post_json(
        "https://api.anthropic.com/v1/messages",
        payload,
        {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    blocks = data.get("content") or []
    text = "\n".join(block.get("text", "") for block in blocks if block.get("type") == "text").strip()
    if not text:
        raise RuntimeError("Claude returned an empty response.")
    return text, latency

from providers.openai_provider import chat as openai_compatible_chat


def chat(messages: list[dict[str, str]], api_key: str, model: str, temperature: float, max_tokens: int, response_format=None, base_url: str = "http://127.0.0.1:8080/v1") -> tuple[str, float]:
    return openai_compatible_chat(
        messages,
        api_key or "local",
        model,
        temperature,
        max_tokens,
        response_format=response_format,
        base_url=base_url,
    )

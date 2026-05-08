from providers.openai_provider import chat as openai_compatible_chat


def chat(messages: list[dict[str, str]], api_key: str, model: str, temperature: float, max_tokens: int, response_format=None) -> tuple[str, float]:
    return openai_compatible_chat(
        messages,
        api_key,
        model,
        temperature,
        max_tokens,
        response_format=response_format,
        base_url="https://openrouter.ai/api/v1",
    )

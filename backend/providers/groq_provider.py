def chat(messages: list[dict[str, str]], api_key: str, model: str, temperature: float, max_tokens: int, response_format=None) -> tuple[str, float]:
    import time

    from groq import Groq

    if not api_key:
        raise RuntimeError("Groq API key is not configured.")

    started = time.perf_counter()
    client = Groq(api_key=api_key)
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        kwargs["response_format"] = response_format
    completion = client.chat.completions.create(**kwargs)
    content = completion.choices[0].message.content.strip()
    if not content:
        raise RuntimeError("Groq returned an empty response.")
    return content, round((time.perf_counter() - started) * 1000, 1)

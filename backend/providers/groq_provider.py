def chat(messages: list[dict[str, str]], api_key: str, model: str, temperature: float, max_tokens: int, response_format=None) -> tuple[str, float]:
    import time

    from groq import Groq

    from providers.groq_limits import remember_groq_headers, remember_groq_rate_limit

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
    try:
        raw_response = client.chat.completions.with_raw_response.create(**kwargs)
        remember_groq_headers(model, raw_response.headers)
        completion = raw_response.parse()
    except Exception as error:
        response = getattr(error, "response", None)
        status_code = getattr(response, "status_code", None)
        if status_code == 429 or "rate_limit" in str(error).lower() or "429" in str(error):
            remember_groq_rate_limit(model, getattr(response, "headers", None), str(error))
        raise
    content = completion.choices[0].message.content.strip()
    if not content:
        raise RuntimeError("Groq returned an empty response.")
    return content, round((time.perf_counter() - started) * 1000, 1)

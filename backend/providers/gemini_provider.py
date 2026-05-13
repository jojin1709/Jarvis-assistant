from providers.http_client import post_json
from providers.base_provider import BrowserAIProvider


def chat(messages: list[dict[str, str]], api_key: str, model: str, temperature: float, max_tokens: int, response_format=None) -> tuple[str, float]:
    system = "\n".join(message["content"] for message in messages if message.get("role") == "system")
    contents = []
    for message in messages:
        if message.get("role") == "system":
            continue
        role = "model" if message.get("role") == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": message.get("content", "")}]})
    payload = {
        "contents": contents,
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    data, latency = post_json(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
        payload,
    )
    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no candidates.")
    parts = ((candidates[0].get("content") or {}).get("parts") or [])
    text = "\n".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise RuntimeError("Gemini returned an empty response.")
    return text, latency


class GeminiBrowserProvider(BrowserAIProvider):
    id = "gemini_web"
    label = "Gemini Web"
    url = "https://gemini.google.com/app"
    login_url = "https://gemini.google.com/app"
    prompt_selectors = (
        "rich-textarea div[contenteditable='true']",
        "div[contenteditable='true']",
        "textarea",
    )
    submit_selectors = (
        "button[aria-label*='Send' i]",
        "button[aria-label*='Submit' i]",
        "button:has(mat-icon:has-text('send'))",
    )
    response_selectors = (
        "message-content",
        ".response-container",
        "model-response",
        "main div:has(p)",
    )
    logged_out_markers = ("sign in", "use gemini", "continue with google")

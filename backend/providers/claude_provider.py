from providers.http_client import post_json
from providers.base_provider import BrowserAIProvider


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


class ClaudeBrowserProvider(BrowserAIProvider):
    id = "claude_web"
    label = "Claude Web"
    url = "https://claude.ai/new"
    login_url = "https://claude.ai/login"
    prompt_selectors = (
        "div[contenteditable='true']",
        "[aria-label*='prompt' i]",
        "textarea",
    )
    submit_selectors = (
        "button[aria-label*='Send' i]",
        "button:has-text('Send')",
        "form button[type='submit']",
    )
    response_selectors = (
        "[data-testid*='message']",
        ".font-claude-message",
        "div.prose",
        "main div:has(p)",
    )
    logged_out_markers = ("sign in", "continue with google", "log in")

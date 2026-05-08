import json

from api.groq_ai import CODE_PROJECT_PROMPT, SYSTEM_PROMPT, chat_groq_messages
from app.config import settings
from providers.config import load_provider_config
from providers.registry import chat_with_provider, provider_key, resolve_provider


def configured_provider() -> str:
    provider = (load_provider_config().get("active_provider") or settings.ai_provider or "auto").strip().lower()
    return provider if provider in {"deepseek", "groq", "nvidia", "sarvam", "openai", "claude", "gemini", "openrouter", "ollama", "local", "local_llamacpp", "auto"} else "auto"


def active_provider() -> str:
    try:
        return resolve_provider("chat")
    except Exception:
        return "groq"


def provider_label() -> str:
    labels = {
        "deepseek": "DeepSeek",
        "groq": "Groq",
        "nvidia": "NVIDIA",
        "sarvam": "Sarvam",
        "openai": "OpenAI",
        "claude": "Claude",
        "gemini": "Gemini",
        "openrouter": "OpenRouter",
        "ollama": "Ollama",
        "local": "Ollama",
        "local_llamacpp": "llama.cpp",
    }
    return labels.get(active_provider(), "Groq")


def _chat_with_provider(
    provider: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    response_format: dict[str, str] | None,
) -> str:
    if provider == "groq" and settings.groq_api_key and not provider_key("groq"):
        return chat_groq_messages(messages, temperature, max_tokens, response_format)
    content, _latency = chat_with_provider(provider, messages, temperature, max_tokens, response_format)
    return content


def chat_ai_messages(
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 700,
    response_format: dict[str, str] | None = None,
    task_type: str = "chat",
) -> str:
    provider = resolve_provider(task_type)
    try:
        return _chat_with_provider(provider, messages, temperature, max_tokens, response_format)
    except Exception as first_error:
        if configured_provider() == "auto":
            for fallback in ("ollama", "local_llamacpp", "groq", "openai", "claude", "gemini", "openrouter"):
                if fallback == provider:
                    continue
                try:
                    return _chat_with_provider(fallback, messages, temperature, max_tokens, response_format)
                except Exception:
                    continue
        raise first_error
        raise


def ask_ai(user_text: str, language_instruction: str = "Reply in English.") -> str:
    try:
        return chat_ai_messages(
            messages=[
                {"role": "system", "content": f"{SYSTEM_PROMPT.strip()}\n{language_instruction}".strip()},
                {"role": "user", "content": user_text},
            ],
            temperature=0.72,
            max_tokens=700,
        )
    except Exception as error:
        return f"{provider_label()} request failed: {error}"


def ask_ai_code_project(user_text: str) -> str:
    try:
        provider = resolve_provider("coding")
    except Exception as error:
        return _code_error_project("missing-provider", str(error))

    try:
        response_format = {"type": "json_object"} if provider in {"deepseek", "groq", "nvidia"} else None
        return chat_ai_messages(
            messages=[
                {"role": "system", "content": CODE_PROJECT_PROMPT.strip()},
                {"role": "user", "content": user_text},
            ],
            temperature=0.35,
            max_tokens=5600,
            response_format=response_format,
            task_type="coding",
        )
    except Exception as error:
        if provider in {"deepseek", "groq", "nvidia"} and ("response_format" in str(error).lower() or "json" in str(error).lower()):
            try:
                return chat_ai_messages(
                    messages=[
                        {"role": "system", "content": CODE_PROJECT_PROMPT.strip()},
                        {"role": "user", "content": user_text},
                    ],
                    temperature=0.35,
                    max_tokens=5600,
                    task_type="coding",
                )
            except Exception as retry_error:
                error = retry_error
        return _code_error_project(
            f"{provider}-request-failed",
            f"{provider_label()} request failed: {error}",
        )


def _code_error_project(project_name: str, message: str) -> str:
    return json.dumps(
        {
            "project_name": project_name,
            "summary": message,
            "files": [{"path": "README.md", "content": message}],
        }
    )

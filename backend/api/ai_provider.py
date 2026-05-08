import json

from api.deepseek_ai import chat_deepseek_messages
from api.groq_ai import CODE_PROJECT_PROMPT, SYSTEM_PROMPT, chat_groq_messages
from api.nvidia_ai import chat_nvidia_messages
from api.sarvam_ai import chat_sarvam_messages
from app.config import settings


def configured_provider() -> str:
    provider = (settings.ai_provider or "groq").strip().lower()
    return provider if provider in {"deepseek", "groq", "nvidia", "sarvam", "auto"} else "groq"


def active_provider() -> str:
    provider = configured_provider()
    if provider == "auto":
        if settings.sarvam_api_key:
            return "sarvam"
        if settings.deepseek_api_key:
            return "deepseek"
        if settings.nvidia_api_key:
            return "nvidia"
        return "groq"
    return provider


def provider_label() -> str:
    labels = {"deepseek": "DeepSeek", "groq": "Groq", "nvidia": "NVIDIA", "sarvam": "Sarvam"}
    return labels.get(active_provider(), "Groq")


def _chat_with_provider(
    provider: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    response_format: dict[str, str] | None,
) -> str:
    if provider == "sarvam":
        return chat_sarvam_messages(messages, temperature, max_tokens, response_format)
    if provider == "deepseek":
        return chat_deepseek_messages(messages, temperature, max_tokens, response_format)
    if provider == "nvidia":
        return chat_nvidia_messages(messages, temperature, max_tokens, response_format)
    return chat_groq_messages(messages, temperature, max_tokens, response_format)


def chat_ai_messages(
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 700,
    response_format: dict[str, str] | None = None,
) -> str:
    provider = active_provider()
    try:
        return _chat_with_provider(provider, messages, temperature, max_tokens, response_format)
    except Exception:
        if configured_provider() == "auto" and provider == "sarvam" and settings.groq_api_key:
            return _chat_with_provider("groq", messages, temperature, max_tokens, response_format)
        if configured_provider() == "auto" and provider == "deepseek" and settings.groq_api_key:
            return _chat_with_provider("groq", messages, temperature, max_tokens, response_format)
        if configured_provider() == "auto" and provider == "nvidia" and settings.groq_api_key:
            return _chat_with_provider("groq", messages, temperature, max_tokens, response_format)
        raise


def ask_ai(user_text: str, language_instruction: str = "Reply in English.") -> str:
    provider = active_provider()
    if provider == "sarvam" and not settings.sarvam_api_key:
        return (
            "Sarvam API key is not configured. Add SARVAM_API_KEY to your .env file, "
            "then restart JX JARVIS."
        )
    if provider == "deepseek" and not settings.deepseek_api_key:
        return (
            "DeepSeek API key is not configured. Add DEEPSEEK_API_KEY to your .env file, "
            "then restart JX JARVIS."
        )
    if provider == "nvidia" and not settings.nvidia_api_key:
        return (
            "NVIDIA API key is not configured. Add NVIDIA_API_KEY to your .env file, "
            "then restart JX JARVIS."
        )
    if provider == "groq" and not settings.groq_api_key:
        return (
            "Groq API key is not configured. Add GROQ_API_KEY to your .env file, "
            "then restart JX JARVIS."
        )

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
    provider = active_provider()
    if provider == "sarvam" and not settings.sarvam_api_key:
        return _code_error_project("missing-sarvam-key", "Add SARVAM_API_KEY to .env, restart JX JARVIS, then ask again.")
    if provider == "deepseek" and not settings.deepseek_api_key:
        return _code_error_project("missing-deepseek-key", "Add DEEPSEEK_API_KEY to .env, restart JX JARVIS, then ask again.")
    if provider == "nvidia" and not settings.nvidia_api_key:
        return _code_error_project("missing-nvidia-key", "Add NVIDIA_API_KEY to .env, restart JX JARVIS, then ask again.")
    if provider == "groq" and not settings.groq_api_key:
        return _code_error_project("missing-groq-key", "Add GROQ_API_KEY to .env, restart JX JARVIS, then ask again.")

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

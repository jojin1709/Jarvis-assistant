import json
import re

from api.groq_ai import CODE_PROJECT_PROMPT, SYSTEM_PROMPT, chat_groq_messages
from app.config import settings
from providers.config import load_provider_config
from providers.groq_limits import groq_model_available
from providers.provider_router import ask_with_orchestration
from providers.registry import PROVIDERS, chat_with_provider, provider_key, resolve_provider

GROQ_CHAT_MODEL_FALLBACKS = [
    "llama-3.1-8b-instant",
    "groq/compound-mini",
    "qwen/qwen3-32b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.3-70b-versatile",
]

GROQ_CODING_MODEL_FALLBACKS = [
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "qwen/qwen3-32b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "groq/compound",
    "groq/compound-mini",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
]


def configured_provider() -> str:
    provider = (load_provider_config().get("active_provider") or settings.ai_provider or "auto").strip().lower()
    return provider if provider in {"deepseek", "groq", "nvidia", "sarvam", "openai", "claude", "gemini", "g4f", "pollinations", "openrouter", "ollama", "local", "local_llamacpp", "chatgpt_web", "claude_web", "gemini_web", "multi_provider", "auto"} else "auto"


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
        "g4f": "G4F",
        "pollinations": "Pollinations",
        "openrouter": "OpenRouter",
        "ollama": "Ollama",
        "local": "Ollama",
        "local_llamacpp": "llama.cpp",
        "chatgpt_web": "ChatGPT Web",
        "claude_web": "Claude Web",
        "gemini_web": "Gemini Web",
        "multi_provider": "Multi-provider",
    }
    return labels.get(active_provider(), "Groq")


def _chat_with_provider(
    provider: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    response_format: dict[str, str] | None,
    model: str | None = None,
) -> str:
    if provider == "groq" and settings.groq_api_key and not provider_key("groq"):
        return chat_groq_messages(messages, temperature, max_tokens, response_format, model=model)
    content, _latency = chat_with_provider(provider, messages, temperature, max_tokens, response_format, model_override=model)
    return content


def chat_ai_messages(
    messages: list[dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 700,
    response_format: dict[str, str] | None = None,
    task_type: str = "chat",
) -> str:
    config = load_provider_config()
    browser_result = _try_browser_orchestration(messages, task_type, config)
    if browser_result:
        return browser_result
    provider = resolve_provider(task_type)
    try:
        if provider == "groq":
            return _chat_groq_with_model_fallbacks(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                models=_groq_models_for_task(task_type, config),
            )
        return _chat_with_provider(provider, messages, temperature, max_tokens, response_format)
    except Exception as first_error:
        errors = [_friendly_provider_error(provider, first_error)]
        if _hybrid_fallback_enabled(config):
            for fallback in _chat_fallback_candidates(config, task_type, provider):
                try:
                    if fallback == "groq":
                        return _chat_groq_with_model_fallbacks(
                            messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            response_format=response_format,
                            models=_groq_models_for_task(task_type, config),
                        )
                    return _chat_with_provider(fallback, messages, temperature, max_tokens, response_format)
                except Exception as fallback_error:
                    errors.append(_friendly_provider_error(fallback, fallback_error))
                    continue
        raise RuntimeError(_summarize_provider_failures(errors)) from first_error


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
    config = load_provider_config()
    browser_result = _try_browser_orchestration(
        [
            {"role": "system", "content": CODE_PROJECT_PROMPT.strip()},
            {"role": "user", "content": user_text},
        ],
        "coding",
        config,
    )
    if browser_result:
        return browser_result
    providers = _token_coding_provider_candidates(config)
    if not providers:
        return _code_error_project(
            "missing-provider",
            "No token-based coding provider is configured. Add an API key in Settings > Providers, enable that provider, then try building the website again.",
        )

    errors = []
    for provider in providers:
        try:
            return _request_code_project(provider, user_text, config)
        except Exception as error:
            errors.append(_friendly_provider_error(provider, error))

    summary = "All configured token API providers failed, so no files were created."
    if errors:
        summary = f"{summary} {' | '.join(errors[:3])}"
    return _code_error_project("coding-provider-request-failed", summary)


def _request_code_project(provider: str, user_text: str, config: dict) -> str:
    response_format = {"type": "json_object"} if provider in {"deepseek", "groq", "nvidia"} else None
    max_tokens = _code_max_tokens(config)
    messages = [
        {"role": "system", "content": CODE_PROJECT_PROMPT.strip()},
        {"role": "user", "content": user_text},
    ]
    if provider == "groq":
        return _chat_groq_with_model_fallbacks(
            messages,
            temperature=0.35,
            max_tokens=max_tokens,
            response_format=response_format,
            models=_groq_models_for_task("coding", config),
        )

    try:
        return _chat_with_provider(
            provider,
            messages,
            temperature=0.35,
            max_tokens=max_tokens,
            response_format=response_format,
        )
    except Exception as error:
        if provider in {"deepseek", "groq", "nvidia"} and ("response_format" in str(error).lower() or "json" in str(error).lower()):
            try:
                return _chat_with_provider(
                    provider,
                    [
                        {"role": "system", "content": CODE_PROJECT_PROMPT.strip()},
                        {"role": "user", "content": user_text},
                    ],
                    temperature=0.35,
                    max_tokens=max_tokens,
                    response_format=None,
                )
            except Exception as retry_error:
                error = retry_error
        raise error


def _chat_groq_with_model_fallbacks(
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    response_format: dict[str, str] | None,
    models: list[str],
) -> str:
    errors = []
    for model in models:
        available, reason = groq_model_available(model)
        if not available:
            errors.append(reason)
            continue
        try:
            return _chat_with_provider(
                "groq",
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                model=model,
            )
        except Exception as error:
            if response_format and ("response_format" in str(error).lower() or "json" in str(error).lower()):
                try:
                    return _chat_with_provider(
                        "groq",
                        messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        response_format=None,
                        model=model,
                    )
                except Exception as retry_error:
                    error = retry_error
            errors.append(f"{model}: {error}")
    raise RuntimeError(_summarize_groq_model_failures(errors))


def _groq_models_for_task(task_type: str, config: dict) -> list[str]:
    configured = str(config.get("models", {}).get("groq") or settings.groq_model or "").strip()
    if task_type == "coding":
        preferred = [*GROQ_CODING_MODEL_FALLBACKS, configured]
    else:
        preferred = [*GROQ_CHAT_MODEL_FALLBACKS, configured]
    models = []
    seen = set()
    for model in preferred:
        if not model or model in seen:
            continue
        seen.add(model)
        models.append(model)
    return models


def _summarize_groq_model_failures(errors: list[str]) -> str:
    if not errors:
        return "Groq request failed for every configured model."
    rate_limited = [error for error in errors if _is_rate_limit_text(error)]
    if len(rate_limited) == len(errors):
        wait = _extract_wait_time(" ".join(errors))
        wait_text = f" Try again in {wait}." if wait else " Try again after the quota window resets."
        return f"Groq rate limit reached for all tried task models.{wait_text}"
    return "Groq request failed for all tried task models. " + " | ".join(errors[:3])


def _resolve_token_coding_provider() -> str:
    providers = _token_coding_provider_candidates(load_provider_config())
    if providers:
        return providers[0]
    raise RuntimeError("No token-based coding provider is configured. Add an API key in Settings > Providers, enable that provider, then try building the website again.")


def _token_coding_provider_candidates(config: dict) -> list[str]:
    active = str(config.get("active_provider") or "auto").strip().lower()
    route = str(config.get("routes", {}).get("coding") or "auto").strip().lower()
    preferred = [provider for provider in (route, active) if provider and provider != "auto"]
    preferred.extend(["groq", "openai", "claude", "gemini", "g4f", "pollinations", "openrouter", "deepseek", "nvidia", "sarvam"])

    candidates = []
    seen = set()
    for provider in preferred:
        if provider in seen:
            continue
        seen.add(provider)
        spec = PROVIDERS.get(provider)
        if not spec or not spec.supports_code or not spec.requires_key:
            continue
        if not config["enabled"].get(provider, False) and provider not in {route, active}:
            continue
        if provider_key(provider) or (provider == "groq" and settings.groq_api_key):
            candidates.append(provider)
    return candidates


def _hybrid_fallback_enabled(config: dict) -> bool:
    active = str(config.get("active_provider") or "auto").strip().lower()
    return active == "auto" or bool(config.get("settings", {}).get("hybrid_mode", True))


def _chat_fallback_candidates(config: dict, task_type: str, failed_provider: str) -> list[str]:
    preferred = [
        "gemini",
        "groq",
        "openai",
        "claude",
        "openrouter",
        "deepseek",
        "nvidia",
        "ollama",
        "local_llamacpp",
        "pollinations",
        "g4f",
    ]
    candidates = []
    for provider in preferred:
        if provider == failed_provider:
            continue
        spec = PROVIDERS.get(provider)
        if not spec or not spec.supports_chat:
            continue
        if task_type == "coding" and not spec.supports_code:
            continue
        if not config["enabled"].get(provider, False):
            continue
        if spec.requires_key and not provider_key(provider) and not (provider == "groq" and settings.groq_api_key):
            continue
        candidates.append(provider)
    return candidates


def _try_browser_orchestration(messages: list[dict[str, str]], task_type: str, config: dict) -> str | None:
    browser_config = config.get("browser_providers", {})
    if not browser_config.get("enabled", False):
        return None
    route = str(browser_config.get("routes", {}).get(task_type) or browser_config.get("routes", {}).get("chat") or "").strip()
    multi = bool(browser_config.get("multi_provider", False)) or route == "multi_provider"
    preferred = None if route in {"", "auto", "multi_provider"} else route
    result = ask_with_orchestration(messages, task_type=task_type, preferred_provider=preferred, multi_provider=multi)
    if result.ok:
        return result.response
    if not browser_config.get("fallback_to_api", True):
        raise RuntimeError(result.error or "Browser provider orchestration failed.")
    return None


def _code_max_tokens(config: dict) -> int:
    try:
        configured = int(config.get("settings", {}).get("code_max_tokens") or 9000)
    except (TypeError, ValueError):
        configured = 9000
    return max(4200, min(configured, 12000))


def _friendly_provider_error(provider: str, error: Exception) -> str:
    label = PROVIDERS.get(provider).label if provider in PROVIDERS else provider.title()
    text = str(error)
    lowered = text.lower()
    if _is_edge_block_text(lowered):
        return (
            f"{label} blocked the request before the model ran (HTTP 403 / error code 1010). "
            "This is provider edge protection, not a Jarvis prompt error."
        )
    if _is_rate_limit_text(lowered):
        wait = _extract_wait_time(text)
        wait_text = f" Wait {wait} and try again." if wait else " Wait for the quota window to reset, or try another provider."
        return f"{label} rate limit reached.{wait_text} Add or enable another API provider key to keep building now."
    if any(marker in lowered for marker in ("api key", "unauthorized", "authentication", "invalid key", "401")):
        return f"{label} API key failed. Check the key in Settings > Providers or enable another token provider."
    if any(marker in lowered for marker in ("timeout", "timed out", "connection", "network")):
        return f"{label} connection failed. Check internet/provider status or enable another token provider."
    compact = re.sub(r"\s+", " ", text).strip()
    return f"{label} request failed: {compact[:260]}"


def _summarize_provider_failures(errors: list[str]) -> str:
    compact_errors = []
    seen = set()
    for error in errors:
        compact = re.sub(r"\s+", " ", str(error)).strip()
        if not compact or compact in seen:
            continue
        seen.add(compact)
        compact_errors.append(compact)
    if not compact_errors:
        return "All configured AI providers failed. Add or enable a working provider key in Settings > AI Providers."
    edge_blocks = [error for error in compact_errors if "error code 1010" in error.lower() or "edge protection" in error.lower()]
    rate_limits = [error for error in compact_errors if _is_rate_limit_text(error)]
    if edge_blocks and len(edge_blocks) == len(compact_errors):
        return (
            "All tried hosted providers were blocked by provider edge protection (HTTP 403 / error code 1010). "
            "Use Gemini/Groq/OpenAI/OpenRouter with a direct API key, or run Ollama locally."
        )
    if rate_limits and len(rate_limits) == len(compact_errors):
        return "All tried providers are rate-limited right now. Wait for quota reset or enable another provider key."
    return "All configured AI providers failed. " + " | ".join(compact_errors[:4])


def _is_edge_block_text(text: str) -> bool:
    lowered = text.lower()
    return "1010" in lowered or "edge protection" in lowered or ("http 403" in lowered and "error code" in lowered)


def _is_rate_limit_text(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in ("rate_limit", "rate limit", "429", "tokens per day", "tpm", "tpd", "rate_limit_exceeded"))


def _extract_wait_time(text: str) -> str:
    match = re.search(r"try again in\s+([^.'\"}]+)", text, flags=re.IGNORECASE)
    if not match:
        return ""
    return match.group(1).strip()


def _code_error_project(project_name: str, message: str) -> str:
    return json.dumps(
        {
            "project_name": project_name,
            "summary": message,
            "files": [],
        }
    )

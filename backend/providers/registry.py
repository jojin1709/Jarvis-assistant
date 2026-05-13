import os
from dataclasses import dataclass
from importlib import import_module

from app.config import settings
from providers.config import load_provider_config, save_provider_config
from providers.groq_limits import groq_limit_snapshot
from providers.ollama_provider import list_models
from providers.secure_store import delete_secret, get_secret, has_secret, masked_secret, save_secret


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    label: str
    module: str
    env_key: str
    kind: str = "cloud"
    supports_chat: bool = True
    supports_code: bool = True
    supports_vision: bool = False
    supports_voice: bool = False
    requires_key: bool = True


PROVIDERS = {
    "groq": ProviderSpec("groq", "Groq", "providers.groq_provider", "GROQ_API_KEY"),
    "openai": ProviderSpec("openai", "OpenAI", "providers.openai_provider", "OPENAI_API_KEY", supports_vision=True),
    "claude": ProviderSpec("claude", "Claude", "providers.claude_provider", "ANTHROPIC_API_KEY"),
    "ollama": ProviderSpec("ollama", "Ollama", "providers.ollama_provider", "", kind="local", requires_key=False),
    "gemini": ProviderSpec("gemini", "Gemini", "providers.gemini_provider", "GEMINI_API_KEY", supports_vision=True),
    "g4f": ProviderSpec("g4f", "G4F", "providers.openai_provider", "G4F_API_KEY"),
    "pollinations": ProviderSpec("pollinations", "Pollinations", "providers.openai_provider", "POLLINATIONS_API_KEY"),
    "openrouter": ProviderSpec("openrouter", "OpenRouter", "providers.openrouter_provider", "OPENROUTER_API_KEY"),
    "local_llamacpp": ProviderSpec("local_llamacpp", "llama.cpp", "providers.local_provider", "", kind="local", requires_key=False),
    "local_whisper": ProviderSpec("local_whisper", "Local Whisper", "", "", kind="local", supports_chat=False, supports_code=False, supports_voice=True, requires_key=False),
    "deepseek": ProviderSpec("deepseek", "DeepSeek", "providers.openai_provider", "DEEPSEEK_API_KEY"),
    "nvidia": ProviderSpec("nvidia", "NVIDIA", "providers.openai_provider", "NVIDIA_API_KEY"),
    "sarvam": ProviderSpec("sarvam", "Sarvam", "providers.openai_provider", "SARVAM_API_KEY", supports_voice=True),
}

BASE_URLS = {
    "deepseek": settings.deepseek_base_url,
    "nvidia": settings.nvidia_base_url,
    "sarvam": f"{settings.sarvam_base_url.rstrip('/')}/v1",
    "g4f": settings.g4f_base_url,
    "pollinations": settings.pollinations_base_url,
}

MODEL_OPTIONS = {
    "groq": [
        "groq/compound",
        "groq/compound-mini",
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "meta-llama/llama-prompt-guard-2-22m",
        "meta-llama/llama-prompt-guard-2-86m",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "openai/gpt-oss-safeguard-20b",
        "qwen/qwen3-32b",
        "whisper-large-v3",
        "whisper-large-v3-turbo",
        "canopylabs/orpheus-arabic-saudi",
        "canopylabs/orpheus-v1-english",
    ],
    "gemini": [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
    ],
    "g4f": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-oss-120b",
        "gpt-oss-20b",
        "gemini-2.5-flash",
        "llama-3.3-70b-versatile",
        "qwen/qwen3-32b",
        "grok-4-fast-non-reasoning",
    ],
    "pollinations": [
        "openai",
    ],
}

TASK_MODEL_PLAN = {
    "groq": {
        "chat": ["llama-3.1-8b-instant", "groq/compound-mini", "qwen/qwen3-32b"],
        "coding": [
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "qwen/qwen3-32b",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "groq/compound",
            "groq/compound-mini",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
        ],
        "safety": ["meta-llama/llama-prompt-guard-2-86m", "meta-llama/llama-prompt-guard-2-22m"],
        "speech_to_text": ["whisper-large-v3-turbo", "whisper-large-v3"],
        "text_to_speech": ["canopylabs/orpheus-v1-english", "canopylabs/orpheus-arabic-saudi"],
    },
    "gemini": {
        "chat": ["gemini-2.5-flash", "gemini-2.5-flash-lite"],
        "coding": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"],
        "vision": ["gemini-2.5-flash", "gemini-2.5-pro"],
        "automation": ["gemini-2.5-flash", "gemini-2.5-flash-lite"],
    },
    "g4f": {
        "chat": ["gpt-4o-mini", "gpt-4o"],
        "coding": ["gpt-4o", "gpt-oss-120b", "gpt-oss-20b"],
        "automation": ["gpt-4o-mini", "gpt-4o"],
    },
    "pollinations": {
        "chat": ["openai"],
        "coding": ["openai"],
        "automation": ["openai"],
    },
}

ENDPOINT_OPTIONS = {
    "g4f": [
        "https://g4f.space/v1",
        "https://g4f.dev/v1",
        "https://g4f.space/api/auto",
        "https://g4f.space/api/groq",
        "https://g4f.space/api/gemini",
        "https://g4f.space/api/nvidia",
        "http://localhost:1337/v1",
    ],
    "pollinations": [
        "https://gen.pollinations.ai/v1",
    ],
}


def provider_key(provider: str) -> str:
    spec = PROVIDERS.get(provider)
    if not spec:
        return ""
    return get_secret(provider) or (os.getenv(spec.env_key, "") if spec.env_key else "")


def list_provider_status() -> dict:
    config = load_provider_config()
    groq_limits = groq_limit_snapshot()
    cards = []
    ollama_models = []
    ollama_latency = None
    try:
        ollama_models, ollama_latency = list_models(config["endpoints"].get("ollama") or settings.ollama_base_url)
    except Exception:
        ollama_models = []
    for provider_id, spec in PROVIDERS.items():
        enabled = bool(config["enabled"].get(provider_id, False))
        has_key = provider_id in {"ollama", "local_llamacpp", "local_whisper"} or bool(provider_key(provider_id))
        cards.append(
            {
                "id": provider_id,
                "label": spec.label,
                "kind": spec.kind,
                "enabled": enabled,
                "connected": enabled and has_key,
                "configured": has_key,
                "maskedKey": masked_secret(provider_id) if spec.requires_key else "",
                "requiresKey": spec.requires_key,
                "model": config["models"].get(provider_id, ""),
                "modelOptions": MODEL_OPTIONS.get(provider_id, []),
                "taskModelPlan": TASK_MODEL_PLAN.get(provider_id, {}),
                "endpoint": config.get("endpoints", {}).get(provider_id, ""),
                "endpointOptions": ENDPOINT_OPTIONS.get(provider_id, []),
                "rateLimits": groq_limits if provider_id == "groq" else {},
                "supports": {
                    "chat": spec.supports_chat,
                    "code": spec.supports_code,
                    "vision": spec.supports_vision,
                    "voice": spec.supports_voice,
                },
                "status": "connected" if enabled and has_key else "missing key" if spec.requires_key else "available",
                "responseSpeedMs": ollama_latency if provider_id == "ollama" and ollama_models else None,
            }
        )
    return {"providers": cards, "config": config, "ollamaModels": ollama_models}


def update_provider_settings(patch: dict) -> dict:
    return save_provider_config(patch)


def set_provider_key(provider: str, key: str) -> None:
    if provider not in PROVIDERS:
        raise RuntimeError("Unsupported provider.")
    save_secret(provider, key)


def remove_provider_key(provider: str) -> None:
    delete_secret(provider)


def resolve_provider(task_type: str = "chat") -> str:
    config = load_provider_config()
    offline = bool(config["settings"].get("offline_mode"))
    route = str(config["routes"].get(task_type) or "auto").lower()
    active = str(config.get("active_provider") or "auto").lower()
    candidates = []
    if route != "auto":
        candidates.append(route)
    if active != "auto":
        candidates.append(active)
    candidates.extend(
        ["ollama", "local_llamacpp"]
        if offline
        else ["gemini", "groq", "openai", "claude", "openrouter", "deepseek", "nvidia", "sarvam", "ollama", "local_llamacpp", "pollinations", "g4f"]
    )
    for provider in candidates:
        if _provider_ready(provider, task_type, config):
            return provider
    raise RuntimeError("No configured AI provider is available. Add a key or enable Ollama/local models.")


def chat_with_provider(provider: str, messages: list[dict[str, str]], temperature: float, max_tokens: int, response_format=None, model_override: str | None = None) -> tuple[str, float]:
    config = load_provider_config()
    spec = PROVIDERS.get(provider)
    if not spec or not spec.supports_chat:
        raise RuntimeError(f"{provider} does not support chat.")
    model = model_override or config["models"].get(provider) or _default_model(provider)
    key = provider_key(provider)
    module = import_module(spec.module)
    kwargs = {}
    if provider in BASE_URLS:
        kwargs["base_url"] = BASE_URLS[provider]
    if provider == "ollama":
        kwargs["base_url"] = config["endpoints"].get("ollama") or settings.ollama_base_url
    if provider == "local_llamacpp":
        kwargs["base_url"] = config["endpoints"].get("local_llamacpp") or "http://127.0.0.1:8080/v1"
    if provider == "g4f":
        kwargs["base_url"] = config["endpoints"].get("g4f") or settings.g4f_base_url
    if provider == "pollinations":
        kwargs["base_url"] = config["endpoints"].get("pollinations") or settings.pollinations_base_url
    return module.chat(messages, key, model, temperature, max_tokens, response_format=response_format, **kwargs)


def test_provider(provider: str, model: str | None = None) -> dict:
    if provider == "local_whisper":
        try:
            import whisper  # noqa: F401
        except ImportError:
            return {
                "ok": False,
                "provider": provider,
                "latencyMs": None,
                "error": "Local Whisper route is available, but the whisper package is not installed.",
            }
        return {"ok": True, "provider": provider, "latencyMs": 0, "message": "Local Whisper is available."}
    config = load_provider_config()
    if model:
        config = save_provider_config({"models": {provider: model}})
    try:
        content, latency = chat_with_provider(
            provider,
            [{"role": "user", "content": "Reply with exactly: JX provider online"}],
            0.1,
            40,
        )
        return {"ok": True, "provider": provider, "latencyMs": latency, "message": content[:240]}
    except Exception as error:
        return {"ok": False, "provider": provider, "latencyMs": None, "error": str(error)}


def ollama_model_list() -> dict:
    config = load_provider_config()
    try:
        models, latency = list_models(config["endpoints"].get("ollama") or settings.ollama_base_url)
        return {"ok": True, "models": models, "latencyMs": latency}
    except Exception as error:
        return {"ok": False, "models": [], "error": str(error)}


def _provider_ready(provider: str, task_type: str, config: dict) -> bool:
    spec = PROVIDERS.get(provider)
    if not spec or not config["enabled"].get(provider, False):
        return False
    if task_type in {"chat", "automation"} and not spec.supports_chat:
        return False
    if task_type == "coding" and not spec.supports_code:
        return False
    if task_type == "vision" and not spec.supports_vision and provider not in {"ollama", "local_llamacpp"}:
        return False
    if task_type == "voice" and not spec.supports_voice:
        return False
    return not spec.requires_key or has_secret(provider) or bool(provider_key(provider))


def _default_model(provider: str) -> str:
    return load_provider_config()["models"].get(provider, "")

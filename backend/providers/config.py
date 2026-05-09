import json
from pathlib import Path


CONFIG_PATH = Path(__file__).resolve().parents[1] / "runtime" / "providers.json"

DEFAULT_PROVIDER_CONFIG = {
    "active_provider": "auto",
    "enabled": {
        "groq": True,
        "openai": False,
        "claude": False,
        "ollama": True,
        "gemini": False,
        "openrouter": False,
        "local_llamacpp": True,
        "local_whisper": True,
        "deepseek": False,
        "nvidia": False,
        "sarvam": False,
    },
    "models": {
        "groq": "llama-3.3-70b-versatile",
        "openai": "gpt-4.1-mini",
        "claude": "claude-3-5-sonnet-latest",
        "ollama": "llama3.1",
        "gemini": "gemini-1.5-flash",
        "openrouter": "openai/gpt-4o-mini",
        "local_llamacpp": "local-model",
        "local_whisper": "base",
        "deepseek": "deepseek-chat",
        "nvidia": "meta/llama-3.1-70b-instruct",
        "sarvam": "sarvam-m",
    },
    "routes": {
        "chat": "auto",
        "coding": "auto",
        "vision": "auto",
        "voice": "auto",
        "automation": "auto",
    },
    "settings": {
        "temperature": 0.72,
        "max_tokens": 700,
        "code_max_tokens": 5600,
        "context_window": 8192,
        "streaming": False,
        "response_style": "professional",
        "offline_mode": False,
        "hybrid_mode": True,
    },
    "endpoints": {
        "ollama": "http://127.0.0.1:11434",
        "local_llamacpp": "http://127.0.0.1:8080/v1",
    },
}


def load_provider_config() -> dict:
    if not CONFIG_PATH.exists():
        return json.loads(json.dumps(DEFAULT_PROVIDER_CONFIG))
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {}
    return _merge(DEFAULT_PROVIDER_CONFIG, data if isinstance(data, dict) else {})


def save_provider_config(patch: dict) -> dict:
    current = load_provider_config()
    merged = _merge(current, patch)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return merged


def _merge(base: dict, patch: dict) -> dict:
    result = json.loads(json.dumps(base))
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result
